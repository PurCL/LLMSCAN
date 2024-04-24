/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_modulo_52a.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-52a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: modulo
 *    GoodSink: Check for zero before modulo
 *    BadSink : Modulo a constant with data
 * Flow Variant: 52 Data flow: data passed as an argument from one function to another to another in three different source files
 *
 * */

#include "std_testcase.h"

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__int_zero_modulo_52b_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_modulo_52_bad()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_modulo_52b_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_modulo_52b_goodG2BSink(int data);

static void goodG2B()
{
    int data;
    /* Initialize data */
    data = -1;
    /* FIX: Use a value not equal to zero */
    data = 7;
    CWE369_Divide_by_Zero__int_zero_modulo_52b_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_modulo_52b_goodB2GSink(int data);

static void goodB2G()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_modulo_52b_goodB2GSink(data);
}

void CWE369_Divide_by_Zero__int_zero_modulo_52_good()
{
    goodG2B();
    goodB2G();
}

#endif /* OMITGOOD */

/* Below is the main(). It is only used when building this testcase on
   its own for testing or for building a binary to use in testing binary
   analysis tools. It is not used when compiling all the testcases as one
   application, which is how source code analysis tools are tested. */

#ifdef INCLUDEMAIN

int main(int argc, char * argv[])
{
    /* seed randomness */
    srand( (unsigned)time(NULL) );
#ifndef OMITGOOD
    printLine("Calling good()...");
    CWE369_Divide_by_Zero__int_zero_modulo_52_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__int_zero_modulo_52_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

    /* POTENTIAL FLAW: Possibly divide by zero */
    printIntLine(100 % data);
    /* POTENTIAL FLAW: Possibly divide by zero */
    printIntLine(100 % data);
    /* FIX: test for a zero denominator */
    if( data != 0 )
    {
        printIntLine(100 % data);
    }
    else
    {
        printLine("This would result in a divide by zero");
    }
    CWE369_Divide_by_Zero__int_zero_modulo_52c_badSink(data);
    CWE369_Divide_by_Zero__int_zero_modulo_52c_goodG2BSink(data);
    CWE369_Divide_by_Zero__int_zero_modulo_52c_goodB2GSink(data);
}