import com.sun.net.httpserver.*;
import java.net.*;
import java.io.*;
import java.lang.instrument.Instrumentation;
import javax.swing.SwingUtilities;
import com.cburch.logisim.proj.*;
import com.cburch.logisim.circuit.*;
import com.cburch.logisim.comp.Component;
import com.cburch.logisim.instance.StdAttr;
import com.cburch.logisim.std.wiring.Pin;
import com.cburch.logisim.data.*;
import java.util.*;
import com.cburch.logisim.comp.ComponentFactory;
import com.cburch.logisim.tools.*;
import com.cburch.logisim.instance.Instance;
import com.cburch.logisim.analyze.model.*;

public class LiveBridge {
 static HttpServer server; static String token; static File workspace;
 public static void agentmain(String args,Instrumentation inst)throws Exception{
  if(server!=null){server.stop(0);server=null;} try { if(LogisimBridge.server!=null){LogisimBridge.server.stop(0);LogisimBridge.server=null;} } catch(Throwable ignored) {}
  String[] a=args.split("\\|",3);token=a[1];workspace=new File(a[2]).getCanonicalFile();
  server=HttpServer.create(new InetSocketAddress("127.0.0.1",Integer.parseInt(a[0])),0);
  server.createContext("/",e->{
   if(!token.equals(e.getRequestHeaders().getFirst("X-Logisim-Token"))){e.sendResponseHeaders(403,-1);e.close();return;}
   if(!e.getRequestMethod().equals("POST")){e.sendResponseHeaders(405,-1);e.close();return;}
   try{
    ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] buf=new byte[4096];int n,total=0;while((n=e.getRequestBody().read(buf))!=-1){total+=n;if(total>16384)throw new IOException("Request too large");b.write(buf,0,n);}
    String data=new String(b.toByteArray(),"UTF-8");String[] result=new String[1];
    SwingUtilities.invokeAndWait(()->{try{result[0]=command(e.getRequestURI().getPath(),data);}catch(Exception ex){result[0]="ERROR: "+ex;}});
    byte[] output=result[0].getBytes("UTF-8");e.getResponseHeaders().set("Content-Type","text/plain; charset=utf-8");e.sendResponseHeaders(result[0].startsWith("ERROR:")?400:200,output.length);e.getResponseBody().write(output);e.close();
   }catch(Exception ex){byte[] o=ex.toString().getBytes("UTF-8");e.sendResponseHeaders(500,o.length);e.getResponseBody().write(o);e.close();}
  });server.setExecutor(null);server.start();
 }
 static Project selected(String name){
  java.util.List<Project> p=Projects.getOpenProjects();
  for(Project x:p)if(x.getLogisimFile().getName().equals(name))return x;
  throw new IllegalArgumentException("Project not found; call list_projects first: "+name);
 }
 static String command(String path,String data)throws Exception{
  if(path.equals("/list")){StringBuilder b=new StringBuilder();for(Project p:Projects.getOpenProjects())b.append(p.getLogisimFile().getName()).append("\t").append(p.getCurrentCircuit().getName()).append("\tdirty=").append(p.isFileDirty()).append("\n");return b.toString();}
  if(path.equals("/open")){
   File f=new File(data).getCanonicalFile();if(!f.toPath().startsWith(workspace.toPath())||!f.getName().endsWith(".circ"))throw new IllegalArgumentException("Only workspace .circ files allowed");
   Project p=ProjectActions.doOpen(null,null,f);return p==null?"ERROR: open cancelled":"Opened "+p.getLogisimFile().getName();
  }
  String[] a=data.split("\n",2);Project p=selected(a[0]);CircuitState s=p.getCircuitState();
  if(path.equals("/inspect")){
   StringBuilder b=new StringBuilder("Circuit: "+p.getCurrentCircuit().getName()+"\n");
   for(Component c:p.getCurrentCircuit().getNonWires()){
    b.append(c.getFactory().getName()).append(" ").append(c.getLocation());
    if(c.getAttributeSet().containsAttribute(StdAttr.LABEL))b.append(" label=").append(c.getAttributeSet().getValue(StdAttr.LABEL));
    if(c.getFactory() instanceof Pin)b.append(" input=").append(Circuit.isInput(c)).append(" value=").append(Pin.FACTORY.getValue(s.getInstanceState(c)).toDisplayString(2));b.append("\n");
   }return b.toString();
  }
  if(path.equals("/inputs")){
   Map<String,Component> pins=new HashMap<>();for(Component c:p.getCurrentCircuit().getNonWires())if(c.getFactory() instanceof Pin && Circuit.isInput(c))pins.put(c.getAttributeSet().getValue(StdAttr.LABEL),c);
   String[] assignments=a[1].split(",");for(String kv:assignments){String[] q=kv.split("=");if(q.length!=2||!pins.containsKey(q[0])||!q[1].matches("[01]"))throw new IllegalArgumentException("Expected existing one-bit input=0 or 1");if(pins.get(q[0]).getEnd(0).getWidth().getWidth()!=1)throw new IllegalArgumentException("Only one-bit inputs supported");}
   for(String kv:assignments){String[] q=kv.split("=");Component c=pins.get(q[0]);Pin.FACTORY.setValue(s.getInstanceState(c),Value.createKnown(BitWidth.ONE,Integer.parseInt(q[1])));s.markComponentAsDirty(c);}
   s.getPropagator().propagate();p.repaintCanvas();return command("/inspect",a[0]);
  }
  return extended(path,p,a.length>1?a[1]:"");
 }
 static ComponentFactory factory(Project p,String library,String name){
  if(library.equals("project")){Circuit c=p.getLogisimFile().getCircuit(name);if(c!=null)return c.getSubcircuitFactory();}
  for(Library lib:p.getLogisimFile().getLibraries())if(lib.getName().equals(library)){Tool t=lib.getTool(name);if(t instanceof AddTool)return ((AddTool)t).getFactory();}
  throw new IllegalArgumentException("Unknown component; use catalog");
 }
 static String id(Component c){return c.getFactory().getName()+"@"+c.getLocation().getX()+","+c.getLocation().getY();}
 static Component find(Project p,String id){for(Component c:p.getCurrentCircuit().getNonWires())if(id(c).equals(id))return c;throw new IllegalArgumentException("Component not found "+id);}
 @SuppressWarnings({"unchecked","rawtypes"})
 static void set(AttributeSet as,String k,String v){Attribute at=as.getAttribute(k);if(at==null||as.isReadOnly(at))throw new IllegalArgumentException("Unknown or read-only attribute "+k);as.setValue(at,at.parse(v));}
 @SuppressWarnings({"unchecked","rawtypes"})
 static String attrs(AttributeSet as){StringBuilder b=new StringBuilder();for(Attribute at:as.getAttributes())b.append(at.getName()).append("=").append(at.toStandardString(as.getValue(at))).append("\n");return b.toString();}
 static void apply(Project p,CircuitMutation m){p.doAction(m.toAction(()->"MCP circuit edit"));p.getSimulator().requestPropagate();p.repaintCanvas();}
 static String extended(String path,Project p,String data)throws Exception{
  Properties a=new Properties();a.load(new StringReader(data));Circuit c=p.getCurrentCircuit();
  if(path.equals("/catalog")){StringBuilder b=new StringBuilder();for(Library lib:p.getLogisimFile().getLibraries()){b.append("LIBRARY ").append(lib.getName()).append("\n");for(Tool t:lib.getTools())b.append("  ").append(t.getName()).append(t instanceof AddTool?" [component]":" [editor tool]").append("\n");}b.append("LIBRARY project\n");for(Circuit cc:p.getLogisimFile().getCircuits())b.append("  ").append(cc.getName()).append(" [subcircuit]\n");return b.toString();}
  if(path.equals("/attributes")){return attrs(factory(p,a.getProperty("library"),a.getProperty("component")).createAttributeSet());}
  if(path.equals("/details")){Component cp=find(p,a.getProperty("id"));StringBuilder b=new StringBuilder(id(cp)+"\n"+attrs(cp.getAttributeSet()));for(com.cburch.logisim.comp.EndData e:cp.getEnds())b.append("port ").append(e.getLocation()).append(" width=").append(e.getWidth().getWidth()).append(" input=").append(e.isInput()).append(" output=").append(e.isOutput()).append("\n");return b.toString();}
  if(path.equals("/add")){
   ComponentFactory f=factory(p,a.getProperty("library"),a.getProperty("component"));AttributeSet as=f.createAttributeSet();
   for(String k:new TreeSet<String>(a.stringPropertyNames()))if(k.startsWith("attr."))set(as,k.substring(5),a.getProperty(k));
   Component cp=f.createComponent(Location.create(Integer.parseInt(a.getProperty("x")),Integer.parseInt(a.getProperty("y"))),as);if(c.hasConflict(cp))throw new IllegalArgumentException("Component conflict");CircuitMutation m=new CircuitMutation(c);m.add(cp);apply(p,m);return id(cp);
  }
  if(path.equals("/wire")){
   CircuitMutation m=new CircuitMutation(c);String[] pts=a.getProperty("points").split(";");if(pts.length<2)throw new IllegalArgumentException("Two points required");
   Location prev=null;for(String pt:pts){String[] xy=pt.split(",");Location next=Location.create(Integer.parseInt(xy[0]),Integer.parseInt(xy[1]));if(prev!=null){if(prev.getX()!=next.getX()&&prev.getY()!=next.getY())throw new IllegalArgumentException("Wire must be orthogonal");if(!prev.equals(next))m.add(Wire.create(prev,next));}prev=next;}apply(p,m);return "Wire path added";
  }
  if(path.equals("/setattr")){
   Component cp=find(p,a.getProperty("id"));AttributeSet clone=(AttributeSet)cp.getAttributeSet().clone();String key=a.getProperty("key");set(clone,key,a.getProperty("value"));CircuitMutation m=new CircuitMutation(c);m.set(cp,clone.getAttribute(key),clone.getValue(clone.getAttribute(key)));apply(p,m);return "Attribute updated";
  }
  if(path.equals("/remove")){Component cp=find(p,a.getProperty("id"));CircuitMutation m=new CircuitMutation(c);m.remove(cp);apply(p,m);return "Component removed; undo available";}
  if(path.equals("/undo")){p.undoAction();return "Undo requested";}
  if(path.equals("/circuits")){StringBuilder b=new StringBuilder();for(Circuit cc:p.getLogisimFile().getCircuits())b.append(cc.getName()).append(cc==c?" [active]":"").append("\n");return b.toString();}
  if(path.equals("/newcircuit")){String name=a.getProperty("name");if(name==null||name.isEmpty()||p.getLogisimFile().getCircuit(name)!=null)throw new IllegalArgumentException("Choose a unique circuit name");Circuit cc=new Circuit(name);p.getLogisimFile().addCircuit(cc);p.getLogisimFile().setDirty(true);p.setCurrentCircuit(cc);return "Created "+name;}
  if(path.equals("/select")){Circuit cc=p.getLogisimFile().getCircuit(a.getProperty("name"));if(cc==null)throw new IllegalArgumentException("Unknown circuit");p.setCurrentCircuit(cc);return "Selected "+cc.getName();}
  if(path.equals("/saveas")){File f=new File(a.getProperty("path")).getCanonicalFile();if(!f.toPath().startsWith(workspace.toPath())||!f.getName().endsWith(".circ")||f.exists())throw new IllegalArgumentException("Use a new workspace .circ path; overwrites disabled");if(!p.getLogisimFile().getLoader().save(p.getLogisimFile(),f))throw new IOException("Save failed");return "Saved "+f;}
  if(path.equals("/simulate")){Simulator sim=p.getSimulator();String action=a.getProperty("action","status");if(action.equals("propagate"))p.getCircuitState().getPropagator().propagate();else if(action.equals("tick"))sim.tick();else if(action.equals("step"))sim.step();else if(action.equals("reset"))sim.requestReset();else if(action.equals("run"))sim.setIsRunning(true);else if(action.equals("pause"))sim.setIsRunning(false);else if(action.equals("ticks_on"))sim.setIsTicking(true);else if(action.equals("ticks_off"))sim.setIsTicking(false);else if(action.equals("frequency")){double hz=Double.parseDouble(a.getProperty("hz"));if(hz<=0||hz>4096)throw new IllegalArgumentException("0 < Hz <= 4096");sim.setTickFrequency(hz);}else if(!action.equals("status"))throw new IllegalArgumentException("Unknown simulator action");p.repaintCanvas();return "running="+sim.isRunning()+" ticking="+sim.isTicking()+" Hz="+sim.getTickFrequency()+" oscillating="+sim.isOscillating();}
  if(path.equals("/analyze")){
   SortedMap<Instance,String> labels=Analyze.getPinLabels(c);List<String> in=new ArrayList<>(),out=new ArrayList<>();
   for(Map.Entry<Instance,String> e:labels.entrySet()){if(Pin.FACTORY.getWidth(e.getKey()).getWidth()!=1)throw new IllegalArgumentException("Classic analyzer requires one-bit pins");(Pin.FACTORY.isInputPin(e.getKey())?in:out).add(e.getValue());}
   if(in.size()>8||out.size()>8)throw new IllegalArgumentException("Analyzer limit 8 inputs and 8 outputs");AnalyzerModel model=new AnalyzerModel();model.setVariables(in,out);model.setCurrentCircuit(p,c);Analyze.computeTable(model,p,c,labels);
   StringBuilder b=new StringBuilder("INPUTS "+in+" OUTPUTS "+out+"\n");TruthTable t=model.getTruthTable();for(int row=0;row<t.getRowCount();row++){for(int col=0;col<t.getInputColumnCount();col++)b.append(t.getInputEntry(row,col).getDescription());b.append(" -> ");for(int col=0;col<t.getOutputColumnCount();col++)b.append(t.getOutputEntry(row,col).getDescription());b.append("\n");}
   for(String name:out)b.append(name).append(" minimal SOP = ").append(model.getOutputExpressions().getMinimalExpression(name)).append("\n");return b.toString();
  }
  throw new IllegalArgumentException("Unknown command");
 }
}
