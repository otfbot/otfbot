/********************************************************************************
*										*
* _niall.c (python module for niall KI)							*
* Copyright 2008 Alexander Schier
*										*
* This program is free software; you can redistribute it and/or modify		*
* it under the terms of the GNU General Public License as published by		*
* the Free Software Foundation; either version 2 of the License, or		*
* (at your option) any later version.						*
*										*
* This program is distributed in the hope that it will be useful,		*
* but WITHOUT ANY WARRANTY; without even the implied warranty of		*
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the			*
* GNU General Public License for more details.					*
*										*
* You should have received a copy of the GNU General Public License		*
* along with this program; if not, write to the Free Software			*
* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.			*
*										*
********************************************************************************/
#include <python2.5/Python.h>
#include "niall.h"

PyObject *print_callback, *warning_callback, *error_callback;
void Niall_Print(char *fmt){
	if(print_callback==NULL) return;
	PyObject *arglist, *result;
	arglist = Py_BuildValue("(s)", fmt);
	result=PyEval_CallObject(print_callback, arglist);
	Py_DECREF(arglist);
}
void Niall_Warning(char *fmt){
	if(warning_callback==NULL) return;
	PyObject *arglist, *result;
	arglist = Py_BuildValue("(s)", fmt);
	result=PyEval_CallObject(warning_callback, arglist);
	Py_DECREF(arglist);
}
void Niall_Error(char *fmt){
	if(error_callback==NULL) return;
	PyObject *arglist, *result;
	arglist = Py_BuildValue("(s)", fmt);
	result=PyEval_CallObject(error_callback, arglist);
	Py_DECREF(arglist);
}

static PyObject *
niall_init(PyObject *self, PyObject *args){
	Niall_Init();
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_free(PyObject *self, PyObject *args){
	Niall_Free();
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_new_dictionary(PyObject *self, PyObject *args){
	Niall_NewDictionary();
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_list_dictionary(PyObject *self, PyObject *args){
	Niall_ListDictionary();
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_save_dictionary(PyObject *self, PyObject *args){
	char *string;
	if(!PyArg_ParseTuple(args, "s", &string)){
		PyErr_SetString(PyExc_TypeError, "no filename parameter given");
		return NULL;
	}
	Niall_SaveDictionary(string);
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_load_dictionary(PyObject *self, PyObject *args){
	char *string;
	if(!PyArg_ParseTuple(args, "s", &string)){
		PyErr_SetString(PyExc_TypeError, "no filename parameter given");
		return NULL;
	}
	Niall_LoadDictionary(string);
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_correct_spelling(PyObject *self, PyObject *args){
	char *string, *string2;
	if(!PyArg_ParseTuple(args, "ss", &string, &string2)){
		PyErr_SetString(PyExc_TypeError, "no filename parameter given");
		return NULL;
	}
	Niall_CorrectSpelling(string, string2);
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_learn(PyObject *self, PyObject *args){
	char *string;
	char *string2=malloc(1024*sizeof(char));

	if(!PyArg_ParseTuple(args, "s", &string)){
		PyErr_SetString(PyExc_TypeError, "learn needs a string as parameter!");
		return NULL;
	}
	strncpy(string2, string, 1024);
	Niall_Learn(string2);
	free(string2); //string(not 2) is freed by python(?)
	Py_INCREF(Py_None);
	return Py_None;
}
static PyObject *
niall_reply(PyObject *self, PyObject *args){
	char *string;
	char *buffer = malloc(1024 * sizeof(char));
	if(!PyArg_ParseTuple(args, "s", &string)){
		PyErr_SetString(PyExc_TypeError, "reply needs a string as parameter!");
		return NULL;
	}
	strncpy(buffer, string, 1024);
	Niall_Reply(buffer, 1024);

	PyObject *answer=Py_BuildValue("s", buffer);
	Py_XINCREF(answer);
	//free(string); //python does this (?)
	free(buffer);
	return answer;
}
static PyObject *
niall_set_callbacks(PyObject *self, PyObject *args)
{
	PyObject *print, *warning, *error;
	if(!PyArg_ParseTuple(args, "OOO", &print, &warning, &error)){
		PyErr_SetString(PyExc_TypeError, "init needs three callback functions!");
		return NULL; /* need three callbacks! */
	}
	if(!(PyCallable_Check(print) && PyCallable_Check(warning) && PyCallable_Check(error))){
		PyErr_SetString(PyExc_TypeError, "One or more callbacks not callable!");
		return NULL; /* need three callbacks! */
	}
	Py_XINCREF(print);
	Py_XDECREF(print_callback);
	Py_XINCREF(warning);
	Py_XDECREF(warning_callback);
	Py_XINCREF(error);
	Py_XDECREF(error_callback);
	print_callback=print;
	warning_callback=warning;
	error_callback=error;

	Py_XINCREF(Py_None);
	return Py_None;
}


int
main(int argc, char *argv[])
{
    /* Pass argv[0] to the Python interpreter */
    Py_SetProgramName(argv[0]);

    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();
	return 0;
}
static PyMethodDef NiallMethods[] = {
	{"init", niall_init, METH_VARARGS, "Init"},
	{"free", niall_free, METH_VARARGS, "Free the Dictionary"},
	{"learn", niall_learn, METH_VARARGS, "Learn a string"},
	{"reply", niall_reply, METH_VARARGS, "Reply to a string"},
	{"new_dictionary", niall_new_dictionary, METH_VARARGS, "Start a new Dictionary"},
	{"save_dictionary", niall_save_dictionary, METH_VARARGS, "Save the Dictionary"},
	{"list_dictionary", niall_list_dictionary, METH_VARARGS, "List the Dictionary"},
	{"load_dictionary", niall_load_dictionary, METH_VARARGS, "Load a Dictionary"},
	{"correct_spelling", niall_correct_spelling, METH_VARARGS, "Corrects a wrong word"},
	{"set_callbacks", niall_set_callbacks, METH_VARARGS, "set the callback functions"},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initniall(void){
    (void) Py_InitModule("niall", NiallMethods);
}
