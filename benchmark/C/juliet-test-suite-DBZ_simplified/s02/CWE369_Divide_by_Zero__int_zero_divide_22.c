/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_22a.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-22a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 22 Control flow: Flow controlled by value of a global variable. Sink functions are in a separate file from sources.
 *
 * */

#include "std_testcase.h"

#ifndef OMITBAD

/* The global variable below is used to drive control flow in the sink function */
int CWE369_Divide_by_Zero__int_zero_divide_22_badGlobal = 0;

void CWE369_Divide_by_Zero__int_zero_divide_22_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_22_bad()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_divide_22_badGlobal = 1; /* true */
    CWE369_Divide_by_Zero__int_zero_divide_22_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* The global variables below are used to drive control flow in the sink functions. */
int CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G1Global = 0;
int CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G2Global = 0;
int CWE369_Divide_by_Zero__int_zero_divide_22_goodG2BGlobal = 0;

/* goodB2G1() - use badsource and goodsink by setting the static variable to false instead of true */
void CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G1Sink(int data);

static void goodB2G1()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G1Global = 0; /* false */
    CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G1Sink(data);
}

/* goodB2G2() - use badsource and goodsink by reversing the blocks in the if in the sink function */
void CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G2Sink(int data);

static void goodB2G2()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G2Global = 1; /* true */
    CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G2Sink(data);
}

/* goodG2B() - use goodsource and badsink */
void CWE369_Divide_by_Zero__int_zero_divide_22_goodG2BSink(int data);

static void goodG2B()
{
    int data;
    /* Initialize data */
    data = -1;
    /* FIX: Use a value not equal to zero */
    data = 7;
    CWE369_Divide_by_Zero__int_zero_divide_22_goodG2BGlobal = 1; /* true */
    CWE369_Divide_by_Zero__int_zero_divide_22_goodG2BSink(data);
}

void CWE369_Divide_by_Zero__int_zero_divide_22_good()
{
    goodB2G1();
    goodB2G2();
    goodG2B();
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
    CWE369_Divide_by_Zero__int_zero_divide_22_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__int_zero_divide_22_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

    if(CWE369_Divide_by_Zero__int_zero_divide_22_badGlobal)
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        printIntLine(100 / data);
    }
    if(CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G1Global)
    {
        /* INCIDENTAL: CWE 561 Dead Code, the code below will never run */
        printLine("Benign, fixed string");
    }
    else
    {
        /* FIX: test for a zero denominator */
        if( data != 0 )
        {
            printIntLine(100 / data);
        }
        else
        {
            printLine("This would result in a divide by zero");
        }
    }
    if(CWE369_Divide_by_Zero__int_zero_divide_22_goodB2G2Global)
    {
        /* FIX: test for a zero denominator */
        if( data != 0 )
        {
            printIntLine(100 / data);
        }
        else
        {
            printLine("This would result in a divide by zero");
        }
    }
    if(CWE369_Divide_by_Zero__int_zero_divide_22_goodG2BGlobal)
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        printIntLine(100 / data);
    }
}