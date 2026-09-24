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

public class LogisimBridge {
 static HttpServer server; static String token; static File workspace;
 public static void agentmain(String args,Instrumentation inst)throws Exception{
  if(server!=null)return;
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
  throw new IllegalArgumentException("Unknown command");
 }
}
