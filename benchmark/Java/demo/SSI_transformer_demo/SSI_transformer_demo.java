package testcases.CWE369_Divide_by_Zero.s04;
import testcasesupport.*;
import java.util.Vector;

import javax.servlet.http.*;

public class ClassA
{
    public ClassA() {

    }

   public int xoo1() throws Throwable {
        IO.writeLine("OK");
        return 1;
   }

   public int xoo2() throws Throwable {
        IO.writeLine("OK");
        return 1;
   }
}

public class CWE369_Divide_by_Zero__int_zero_divide_72a extends AbstractTestCase
{
    public void foo2() throws Throwable
    {
        int data;

        data = 0;

        hoo(data);
    }

    public void hoo(int a) throws Throwable
    {
        int data = a;

        IO.writeLine("foo2: 100/" + data + " = " + (100 / data) + "\n");
    }

    public void goo1(int a, int b, int c) throws Throwable
    {
        int data = a;

        if (data != 0)
        {
            IO.writeLine("100/" + data + " = " + (100 / data) + "\n");
        }
        else
        {
            IO.writeLine("This would result in a divide by zero");
        }
    }

    private void foo1() throws Throwable
    {
        int data;
        data = 0;

        ClassA a = new ClassA();

        goo1(data, a.xoo1(), a.xoo2());
    }

    /* goo2() - use BadSource and GoodSink */
    private void goo2() throws Throwable
    {
        int data;

        data = 0;

        hoo(data);
    }


    public void good() throws Throwable
    {
        foo1();
        foo2();
    }

    public static void main(String[] args) throws ClassNotFoundException,
           InstantiationException, IllegalAccessException
    {
        good();
    }
}