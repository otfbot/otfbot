/* $Id: python-interface.c,v 1.7 2004/01/13 10:59:20 lfousse Exp $ */
/* MegHAL Python interface, by David N. Welton <davidw@dedasys.com> */

#include <Python.h>
#include "megahal.h"
#include <stdio.h>

static PyObject *mhinitbrain(PyObject *self, PyObject *args)
{
    megahal_initialize();
	return Py_BuildValue("");
}

static PyObject *mhdoreply(PyObject *self, PyObject *args)
{
    char *input;
    char *output = NULL;

    if (!PyArg_ParseTuple(args, "s", &input))
	return NULL;

    output = megahal_do_reply(input, 1);

    return PyString_FromString(output);
}

static PyObject *mhlearn(PyObject *self, PyObject *args)
{
    char *input;

    if (!PyArg_ParseTuple(args, "s", &input))
	return NULL;

    megahal_learn_no_reply(input, 1);

	return Py_BuildValue("");
}

static PyObject *mhcleanup(PyObject *self, PyObject *args)
{
    megahal_cleanup();
	return Py_BuildValue("");
}

static PyObject *mhsetnobanner(PyObject *self, PyObject *args)
{
    megahal_setnobanner();
	return Py_BuildValue("");
}

static PyObject *mhseterrorfile(PyObject *self, PyObject *args)
{
    char *input;
    
    if (!PyArg_ParseTuple(args, "s", &input))
	return NULL;

    megahal_seterrorfile(input);
	return Py_BuildValue("");
}

static PyObject *mhsetstatusfile(PyObject *self, PyObject *args)
{
    char *input;
    
    if (!PyArg_ParseTuple(args, "s", &input))
	return NULL;
    megahal_setstatusfile(input);
	return Py_BuildValue("");
}

static PyObject *mhsetdir(PyObject *self, PyObject *args)
{
    char *input;
    
    if (!PyArg_ParseTuple(args, "s", &input))
	return NULL;

    megahal_setdirectory(input);
	return Py_BuildValue("");
}

static struct PyMethodDef mh_methods[] = {
    {"initbrain", mhinitbrain, METH_VARARGS, "Initialize megahal brain"},
    {"doreply", mhdoreply, METH_VARARGS, "Generate a reply"},
    {"cleanup", mhcleanup, METH_VARARGS,"Clean megahal"},
    {"learn", mhlearn, METH_VARARGS, "Learn from a sentence, don't generate a reply"},
    {"setnobanner", mhsetnobanner, METH_VARARGS, "Turns off Banner"},
    {"seterrorfile", mhseterrorfile, METH_VARARGS, "Set Errorfile"},
    {"setstatusfile", mhsetstatusfile, METH_VARARGS, "Set Statusfile"},
    {"setdir", mhsetdir, METH_VARARGS, "Set Directory for saving brains etc"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

void initmh_python()
{
    Py_InitModule("mh_python", mh_methods);

    if(PyErr_Occurred())
	Py_FatalError("can't initialize module my_python");
}
