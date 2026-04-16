# PyLator – C to Python Transcompiler

## Overview
PyLator is a source-to-source transcompiler that converts **C programs into equivalent Python code** using core principles of **Compiler Design**.

C and Python are two of the most widely used programming languages:
- **C** → Fast, efficient, hardware-level control  
- **Python** → Simple, readable, rich libraries  

Many developers start with C but later switch to Python for domains like Data Science, Machine Learning, and Web Development. Rewriting code manually is time-consuming, so PyLator automates this process.

---

## Project Objectives

The main goal is to design and implement a transcompiler that:
- Converts C code into Python code
- Preserves the original logic
- Uses compiler design phases

### Specific Goals:
1. Understand syntax of C and Python  
2. Implement compiler phases:
   - Lexical Analysis  
   - Syntax Analysis  
   - Code Generation  
3. Generate correct Python output without logic change  

---

## How It Works

PyLator follows compiler design architecture:

C Code → Lexer → Parser → Intermediate Representation → Code Generator → Python Code

### Phases:

**1. Lexical Analysis**
- Breaks code into tokens (keywords, identifiers, operators)

**2. Syntax Analysis**
- Builds structure using grammar rules

**3. Code Generation**
- Converts structure into Python syntax

---

## Features

- Converts basic C programs to Python  
- Preserves logical flow  
- Modular compiler design  
- Beginner-friendly  
- Open-source  

---
