/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_zero_65a.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-65a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 65 Data/control flow: data passed as an argument from one function to a function in a different source file called via a function pointer
 *
 * */

#include "std_testcase.h"

#include <math.h>

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__float_zero_65b_badSink(float data);

void CWE369_Divide_by_Zero__float_zero_65_bad()
{
    float data;
    /* define a function pointer */
    void (*funcPtr) (float) = CWE369_Divide_by_Zero__float_zero_65b_badSink;
    /* Initialize data */
    data = 0.0F;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0.0F;
    /* use the function pointer */
    funcPtr(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_zero_65b_goodG2BSink(float data);

static void goodG2B()
{
    float data;
    void (*funcPtr) (float) = CWE369_Divide_by_Zero__float_zero_65b_goodG2BSink;
    /* Initialize data */
    data = 0.0F;
    /* FIX: Use a hardcoded number that won't a divide by zero */
    data = 2.0F;
    funcPtr(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_zero_65b_goodB2GSink(float data);

static void goodB2G()
{
    float data;
    void (*funcPtr) (float) = CWE369_Divide_by_Zero__float_zero_65b_goodB2GSink;
    /* Initialize data */
    data = 0.0F;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0.0F;
    funcPtr(data);
}

void CWE369_Divide_by_Zero__float_zero_65_good()
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
    CWE369_Divide_by_Zero__float_zero_65_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__float_zero_65_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

#endif
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_zero_65b.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-65b.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 65 Data/control flow: data passed as an argument from one function to a function in a different source file called via a function pointer
 *
 * */



#ifndef OMITBAD

void CWE369_Divide_by_Zero__float_zero_65b_badSink(float data)
{
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_zero_65b_goodG2BSink(float data)
{
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_zero_65b_goodB2GSink(float data)
{
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
}

#endif /* OMITGOOD */
