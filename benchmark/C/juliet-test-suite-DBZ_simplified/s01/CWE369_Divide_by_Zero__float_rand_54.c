/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_rand_54a.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-54a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: rand Set data to result of RAND32(), which may be zero
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */

#include "std_testcase.h"

#include <math.h>

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__float_rand_54b_badSink(float data);

void CWE369_Divide_by_Zero__float_rand_54_bad()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    /* POTENTIAL FLAW: Use a random number that could possibly equal zero */
    data = (float)RAND32();
    CWE369_Divide_by_Zero__float_rand_54b_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_rand_54b_goodG2BSink(float data);

static void goodG2B()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    /* FIX: Use a hardcoded number that won't a divide by zero */
    data = 2.0F;
    CWE369_Divide_by_Zero__float_rand_54b_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_rand_54b_goodB2GSink(float data);

static void goodB2G()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    /* POTENTIAL FLAW: Use a random number that could possibly equal zero */
    data = (float)RAND32();
    CWE369_Divide_by_Zero__float_rand_54b_goodB2GSink(data);
}

void CWE369_Divide_by_Zero__float_rand_54_good()
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
    CWE369_Divide_by_Zero__float_rand_54_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__float_rand_54_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

    CWE369_Divide_by_Zero__float_rand_54c_badSink(data);
    CWE369_Divide_by_Zero__float_rand_54c_goodG2BSink(data);
    CWE369_Divide_by_Zero__float_rand_54c_goodB2GSink(data);
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
    /* FIX: Check for value of or near zero before dividing */
    if(fabs(data) > 0.000001)
    {
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
    else
    {
        printLine("This would result in a divide by zero");
    }
    CWE369_Divide_by_Zero__float_rand_54e_badSink(data);
    CWE369_Divide_by_Zero__float_rand_54e_goodG2BSink(data);
    CWE369_Divide_by_Zero__float_rand_54e_goodB2GSink(data);
    CWE369_Divide_by_Zero__float_rand_54d_badSink(data);
    CWE369_Divide_by_Zero__float_rand_54d_goodG2BSink(data);
    CWE369_Divide_by_Zero__float_rand_54d_goodB2GSink(data);
}