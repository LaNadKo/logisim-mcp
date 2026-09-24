import com.sun.tools.attach.VirtualMachine;
public class Attach {
 public static void main(String[] a)throws Exception {
  if(a.length==1&&a[0].equals("--list")) {
   for(com.sun.tools.attach.VirtualMachineDescriptor vm:VirtualMachine.list())System.out.println(vm.id()+"\t"+vm.displayName());
   return;
  }
  if(a.length!=3)throw new IllegalArgumentException("Expected --list or PID JAR OPTIONS");
  VirtualMachine vm=VirtualMachine.attach(a[0]);
  try{vm.loadAgent(a[1],a[2]);}finally{vm.detach();}
  System.out.println("Attached to Logisim PID "+a[0]);
 }
}
