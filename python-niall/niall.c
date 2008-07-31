/********************************************************************************
*										*
* niall.c (part of gNiall)							*
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
// some "fprintf(stderr, ..." commented out by Alexander Schier

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

#include "niall.h"


/********************************************************************************
* Definitions and structures							*
********************************************************************************/

#define END_SENTENCE	NULL
#define FILE_ID		"NIALL2"

typedef struct word WORD;
typedef struct ascn ASCN;
struct word
{
	WORD	*Next;
	char	*Data;
	ASCN	*Associations;
};
struct ascn
{
	ASCN	*Next;
	int	Word;
	int	Probability;
};

WORD *WordList;

extern void Niall_Print( char *fmt, ... );
extern void Niall_Warning( char *fmt, ... );
extern void Niall_Error( char *fmt, ... );


/********************************************************************************
* Linked List Handlers								*
********************************************************************************/

/* Add a new word to the list
*/
static WORD *AddWord(char *Data)
{
	WORD *Word,*Last;

	for(Last=NULL,Word=WordList;Word;Word=Word->Next) Last=Word;

	Word=calloc(sizeof(WORD),1);
	if(!Word) return(NULL);

	Word->Data=calloc(sizeof(char),strlen(Data)+1);
	if(!Word->Data) return(NULL);
	strcpy(Word->Data,Data);

	if(Last)
		Last->Next=Word;
	else
		WordList=Word;

	return(Word);
}

/* Return pointer to a word in the list
*/
static WORD *FindWord(char *Data)
{
	WORD *Word;

	for(Word=WordList;Word;Word=Word->Next)
	{
		if(!strcmp(Word->Data,Data)) return(Word);
	}
	return(NULL);
}

/* Return the index of a word
*/
static int WordIndex(WORD *This)
{
	WORD *Word;
	int i;

	for(i=0,Word=WordList;Word;Word=Word->Next,i++)
	{
		if(Word==This) return(i);
	}
	return(-1);
}

/* Return ptr to word number #
*/
static WORD *GetWord(int Index)
{
	WORD *Word;
	int i;

	for(i=0,Word=WordList;Word;Word=Word->Next,i++)
	{
		if(i==Index) return(Word);
	}
	return(NULL);
}

/* Count probabilities on a word
*/
static int CountProbs(WORD *Word)
{
	ASCN *Assoc;
	int total;

	for(total=0,Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
	{
		total+=Assoc->Probability;
	}
	return(total);
}

/* Count the words in the dictionary
*/
static int CountWords(void)
{
	WORD *Word;
	int i;

	for(i=0,Word=WordList;Word;Word=Word->Next,i++);
	return(i);
}


/********************************************************************************
* Learning Functions								*
********************************************************************************/

/* Associate a word with one that follows it.
*/
static void Associate(WORD *Word,int Next)
{
	ASCN *Assoc;

	for(Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
	{
		if(Assoc->Word==Next)
		{
			Assoc->Probability++;
			return;
		}
	}

	Assoc=calloc(sizeof(ASCN),1);
	if(!Assoc) Niall_Error("Out of memory.");

	Assoc->Word = Next;
	Assoc->Probability = 1;
	Assoc->Next = Word->Associations;
	Word->Associations = Assoc;
}

/* Add one word to the dictionary.
*/
static int IndexWord(char *Word,int Follows)
{
	WORD *thisWord,*lastWord;
	int wordIndex;

	if(Word != END_SENTENCE)
	{
		thisWord = FindWord(Word);
		if(!thisWord)
		{
			thisWord = AddWord(Word);
			if(!thisWord) Niall_Error("Out of memory.");
		}
		wordIndex = WordIndex(thisWord);	
	}
	else wordIndex = -1;

	lastWord = GetWord(Follows);
	if(!lastWord) Niall_Error("Corrupted brain (Can't find last word).");
	Associate(lastWord,wordIndex);

	return(wordIndex);
}

/* Add the words in a processed sentence to the dictionary.
*/
static void AddWords(char *Buffer)
{
	int LastWord=0;
	int i;

	while(strlen(Buffer))
	{
		while(isspace(*Buffer)) Buffer++;
		for(i=0;(!isspace(Buffer[i]))&&(Buffer[i]!=0);i++);

		if(strlen(Buffer)==0)	/* No more words */
		{
			if(LastWord) IndexWord(END_SENTENCE,LastWord);
		}
		else if(Buffer[i]==0)
		{
			LastWord=IndexWord(Buffer,LastWord);
			IndexWord(END_SENTENCE,LastWord);
			Buffer += i;
		}
		else
		{
			Buffer[i] = 0;
			LastWord = IndexWord(Buffer,LastWord);
			Buffer += (i+1);
		}
	}
}

/* Process a line of text
*/
void Niall_Learn(char *Buffer)
{
	char c;
	int i,j;

	/* Remove trailing spaces
	*/
	for(i=strlen(Buffer)-1;i>=0;i--)
	{
		if(!isspace(Buffer[i])) break;
		Buffer[i]=0;
	}

	/* Strip punctuation and break sentence if necessary
	*/
	for(i=0;i<strlen(Buffer);i++)
	{
		c=Buffer[i];

		if(( c=='.' )||( c==',' ))
		{
			if( i+1 < strlen(Buffer))
			{
				Buffer[i]=0;
				Niall_Learn(&Buffer[i+1]);
			}
			Buffer[i]=0;
			break;
		}
		else if(isspace(c))
		{
			Buffer[i]=' ';
		}
		else if(!isalnum(c))
		{
			for(j=i+1;j<=strlen(Buffer);j++) Buffer[j-1]=Buffer[j];
			i--;
		}
		else Buffer[i]=tolower(c);
	}
	AddWords(Buffer);
}


/********************************************************************************
* Speaking Functions								*
********************************************************************************/

/* Add a string to the end of the buffer, checking for overflows.
*/
static void safeStrcat(char *Buffer,int BufSize,char *Word)
{
	int i;

        //fprintf(stderr, "« %s » and « %s »\n", Buffer, Word);
	if((strlen(Buffer)+strlen(Word)+1)>BufSize)
	{
                //fprintf(stderr, "FUCK ! overflow\n");
		Niall_Warning("Buffer overflow - %d bytes exceeded.",BufSize);

		for(i=strlen(Buffer);i<BufSize;i++) { fprintf(stderr, "blork\n"); Buffer[i]='<'; }
		Buffer[BufSize-1]=0;
	}
	else
	{
                //fprintf(stderr, "OK - strcat\n");
		strcat(Buffer,Word);
	}
        //fprintf(stderr, "blorked\n");
}

/* Add the next word on to the end of the buffer
*/
static void StringWord(char *Buffer,int BufSize,WORD *ThisWord)
{
	int nProbs,iProb,total;
	WORD *NextWord;
	ASCN *Assoc;

	/* Randomly select an index for the next word.
	*/
	nProbs = CountProbs(ThisWord);
	if(nProbs<1)
	{
		Niall_Warning("Corrupted brain (Unlinked word).");
		return;
	}

	/* Taken from the rand(3) manual page...
	*/
	iProb = (int)( (float)nProbs*(float)rand() / ((float)RAND_MAX+1.0) );

	/* Find the next word.
	*/
	for(total=0,Assoc=ThisWord->Associations;Assoc;Assoc=Assoc->Next)
	{
		total+=Assoc->Probability;
		if(total>iProb)
		{
			NextWord = GetWord(Assoc->Word);
			if(NextWord != END_SENTENCE)
			{
				if(strlen(Buffer)) safeStrcat(Buffer,BufSize," ");
				safeStrcat(Buffer,BufSize,NextWord->Data);
				StringWord(Buffer,BufSize,NextWord);
				return;
			}
			else return;
		}
	}
	Niall_Warning("Corrupted brain (Loop Overflow).");
}

/* Say something!
*/
void Niall_Reply(char *Buffer,int BufSize)
{
	WORD *Word;

	/* Clear the buffer.
	*/
	Buffer[0]=0;

	/* Check we have some words to say
	*/
	if(WordList==NULL)
	{
		Niall_Warning("Corrupted brain (Not initialised).");
		Niall_NewDictionary();
		return;
	}
	if(CountProbs(WordList)==0)
	{
		strcpy(Buffer,"I cannot speak yet!");
		return;
	}

	/* Speak some words of wisdom.
	*/
	StringWord(Buffer,BufSize,WordList);
	Buffer[0]=toupper(Buffer[0]);
        //fprintf(stderr, "speaking 1\n");
	safeStrcat(Buffer,BufSize,".");
        //fprintf(stderr, "speaking 2\n");
}


/********************************************************************************
* Housekeeping Functions							*
********************************************************************************/

/* Clear any words in the dictionary
*/
static void ClearDictionary(void)
{
	WORD *thisWord,*nextWord;
	ASCN *thisAscn,*nextAscn;

	for(thisWord=WordList;thisWord;thisWord=nextWord)
	{
		for(thisAscn=thisWord->Associations;thisAscn;thisAscn=nextAscn)
		{
			nextAscn=thisAscn->Next;
			free(thisAscn);
		}
		nextWord=thisWord->Next;
		free(thisWord);
	}
	WordList=NULL;
}

/* Create a new, blank dictionary
*/
void Niall_NewDictionary(void)
{
	ClearDictionary();

	WordList=AddWord("");
	if(!WordList) Niall_Error("Out of memory.");
}

/* List the dictionary
*/
void Niall_ListDictionary(void)
{
	WORD *Word;
	ASCN *Assoc;
	int i;

	Niall_Print("\n");
	for(i=0,Word=WordList;Word;Word=Word->Next,i++)
	{
		if(strlen(Word->Data)==0)
			Niall_Print("%4d: > %d|",i,CountProbs(Word));
		else
			Niall_Print("%4d: %s %d|",i,Word->Data,CountProbs(Word));
		for(Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
		{
			Niall_Print(" %d(%d)",Assoc->Word,Assoc->Probability);
		}
		Niall_Print("\n");
	}
	Niall_Print("\n");
}

/* Save the dictionary
*/
void Niall_SaveDictionary(char *FileName)
{
	FILE *fHandle;
	int nWords;
	WORD *Word;
	ASCN *Assoc;
	int i;

	nWords=CountWords();
	if(nWords<2)
	{
		Niall_Warning("No words to save.");
		return;
	}

	fHandle=fopen(FileName,"w");
	if(!fHandle)
	{
		Niall_Warning("Can't open file %s.",FileName);
		return;
	}
	fprintf(fHandle,"%s %d\n",FILE_ID,nWords);

	for(i=0,Word=WordList;Word;Word=Word->Next,i++)
	{
		if(strlen(Word->Data)==0)
			fprintf(fHandle,"%4d: > %d|",i,CountProbs(Word));
		else
			fprintf(fHandle,"%4d: %s %d|",i,Word->Data,CountProbs(Word));
		for(Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
		{
			fprintf(fHandle," %d(%d)",Assoc->Word,Assoc->Probability);
		}
		fprintf(fHandle,"\n");
		if(ferror(fHandle))
		{
			Niall_Warning("File %s not saved correctly.",FileName);
			fclose(fHandle);
			return;
		}
	}
	fclose(fHandle);
}

/* Load a dictionary
*/
void Niall_LoadDictionary(char *FileName)
{
	char Buffer[BUFSIZ];
	FILE *fHandle;
	int nWords,i,d;
	int nAsocs,j,w,p,k;
	WORD *Word;

	fHandle=fopen(FileName,"r");
	if(!fHandle)
	{
		Niall_Warning("File %s not found.",FileName);
		return;
	}
	fscanf(fHandle,"%s %d\n",Buffer,&nWords);
	if((strcmp(Buffer,FILE_ID))||(nWords<2))
	{
		Niall_Warning("File %s is not a valid Niall file.",FileName);
		return;
	}
	ClearDictionary();

	for(i=0;i<nWords;i++)
	{
		fscanf(fHandle,"%4d: %s %d|",&d,Buffer,&nAsocs);
		if((d!=i)||(nAsocs<1))
		{
			Niall_Warning("Word %d is corrupted.",i);
			Niall_NewDictionary();
			return;
		}
		if(Buffer[0]=='>')
		{
			if(i!=0)
			{
				Niall_Warning("Word %d is corrupted.",i);
				Niall_NewDictionary();
				return;
			}
			Buffer[0]=0;
		}
		Word=AddWord(Buffer);
		if(Word==NULL) Niall_Error("Out of memory.");

		for(j=0;j<nAsocs;)
		{
			fscanf(fHandle," %d(%d)",&w,&p);
			if(w>=nWords)
			{
				Niall_Warning("Word %d/Assoc %d is corrupted.",i,j);
				Niall_NewDictionary();
				return;
			}
			for(k=0;k<p;k++) Associate(Word,w);
			j+=p;
		}
	}
}

/* Remove punctuation from a word
*/
static void StripPunctuation(char *Buffer)
{
	char c;
	int i,j;

	/* Strip punctuation and remove extra words
	*/
	for(i=0;i<strlen(Buffer);i++)
	{
		c=Buffer[i];

		if(( c=='.' )||( c==',' )||(isspace(c)))
		{
			Buffer[i]=0;
			break;
		}
		else if(!isalnum(c))
		{
			for(j=i+1;j<=strlen(Buffer);j++) Buffer[j-1]=Buffer[j];
			i--;
		}
		else Buffer[i]=tolower(c);
	}
}

/* Correct a spelling
*/
void Niall_CorrectSpelling(char *Original, char *Correct)
{
	WORD *OrigWord,*CorrWord,*Word;
	int OrigIndex,CorrIndex;
	ASCN *Assoc,*nextAscn,*prevAscn;
	int i;

	/* Clean up the words
	*/
	StripPunctuation(Original);
	StripPunctuation(Correct);

	/* Check they are not empty
	*/
	if((strlen(Original)==0)||(strlen(Correct)==0))
	{
		Niall_Warning("You must enter a word to be corrected and a corrected version.");
		return;
	}

	/* Check they aren't the same
	*/
	if(!strcmp(Original,Correct))
	{
		Niall_Warning("The words are the same!");
		return;
	}

	/* Find the original (mis-spelt) word
	*/
	OrigWord=FindWord(Original);
	if(OrigWord==NULL)
	{
		Niall_Warning("Can't find word '%s' in dictionary.",Original);
		return;
	}

	/* Check if the corrected version already exists
	*/
	CorrWord=FindWord(Correct);
	if(CorrWord==NULL)
	{
		/* This is the easy one. Just replace the word.
		*/
		free(OrigWord->Data);
		OrigWord->Data = calloc(sizeof(char),strlen(Correct)+1);
		strcpy(OrigWord->Data,Correct);
	}
	else
	{
		/* More complex. Any links to the incorrect word must be
		** destroyed and re-made for the correct word. Links from
		** the incorrect word must be applied to the correct word.
		** The incorrect word must be removed from the dictionary,
		** and all links updated to reflect the change of index.
		*/
		OrigIndex = WordIndex(OrigWord);
		CorrIndex = WordIndex(CorrWord);

		/* Recreate associations to the incorrect word.
		*/
		for(Word=WordList;Word;Word=Word->Next)
		{
			for(Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
			{
				if(Assoc->Word != OrigIndex) continue;

				/* Unlink the association.
				*/
				if(Assoc == Word->Associations)
				{
					Word->Associations = Assoc->Next;
				}
				else
				{
					for(prevAscn=Word->Associations;prevAscn;prevAscn=prevAscn->Next)
					{
						if(Assoc == prevAscn->Next)
						{
							prevAscn->Next = Assoc->Next;
							break;
						}
					}
				}

				/* Re-make the association on the correct word
				*/
				for(i=0;i<Assoc->Probability;i++) Associate(Word,CorrIndex);

				/* Free the association.
				*/
				free(Assoc);
				break;
			}
		}


		/* Copy old associations to the correct word.
		*/
		for(Assoc=OrigWord->Associations;Assoc;Assoc=Assoc->Next)
		{
			for(i=0;i<Assoc->Probability;i++) Associate(CorrWord,Assoc->Word);
		}


		/* Delete the old associations.
		*/
		for(Assoc=OrigWord->Associations;Assoc;Assoc=nextAscn)
		{
			nextAscn=Assoc->Next;
			free(Assoc);
		}
		OrigWord->Associations=NULL;


		/* Unlink and free the old word.
		*/
		if(OrigWord == WordList)
		{
			WordList = OrigWord->Next;
		}
		else
		{
			for(Word=WordList;Word;Word=Word->Next)
			{
				if(OrigWord == Word->Next)
				{
					Word->Next = OrigWord->Next;
					break;
				}
			}
		}
		free(OrigWord->Data);
		free(OrigWord);


		/* Update the indexes in all associations.
		*/
		for(Word=WordList;Word;Word=Word->Next)
		{
			for(Assoc=Word->Associations;Assoc;Assoc=Assoc->Next)
			{
				if(Assoc->Word > OrigIndex) Assoc->Word--;
			}
		}
	}
}


/********************************************************************************
* Startup/Shutdown functions							*
********************************************************************************/

void Niall_Init(void)
{
	srand(time(NULL));
	Niall_NewDictionary();
}

void Niall_Free(void)
{
	ClearDictionary();
}

/*******************************************************************************/
