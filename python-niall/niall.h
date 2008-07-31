/********************************************************************************
*										*
* niall.h (part of gNiall)							*
* Copyright 1999 Gary Benson <rat@spunge.org>					*
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
*********************************************************************************
*										*
* NB. In addition to the functions that niall.c provides, it expects		*
*   the following external functions:						*
*										*
* void Niall_Print( char *fmt, ... );	 -  Print a line of text		*
* void Niall_Warning( char *fmt, ... );	 -  Non fatal error (returns)		*
* void Niall_Error( char *fmt, ... );	 -  Fatal error (must not return)	*
*										*
********************************************************************************/

#ifndef NIALL_H_INCLUDED
#define NIALL_H_INCLUDED

/* Startup/shutdown code.
*/
void Niall_Init(void);
void Niall_Free(void);

/* Niall's main functions.
*/
void Niall_Learn(char *Buffer);
void Niall_Reply(char *Buffer,int BufSize);

/* Housekeeping functions.
*/
void Niall_NewDictionary(void);
void Niall_ListDictionary(void);
void Niall_SaveDictionary(char *file);
void Niall_LoadDictionary(char *file);
void Niall_CorrectSpelling(char *Original,char *Correct);

#endif

/*******************************************************************************/

