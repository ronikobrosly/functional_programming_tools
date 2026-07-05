# Batch ETL Job

## Purpose
This is meant to be a toy/example python app to perform a typical, batch ETL-type workflow. The purpose is to demonstrate how such a job could be done with a functional programming paradigm. 

## Functional Programming Guidelines
Please see the `FUNC_PROG_GUIDE.md` file for specifics on how the user would like the app implemented. 

## App description 
This is meant to be a functioning toy app that is relatively minimal but still actually runs. This app is meant to be scheduled and run a few times a day. Don't worry about the mechanism for running the app; assume this is taken care of somehow. 

The basic flow of the app is:

```
"Job begins" -> "Pulls data from the web" -> "Does light transformations" -> "Saves data to in-memory SQLite"
```
The app will be run with an argument that specifies which job type will be run. There will be two types of batch jobs that will be run. Depending on what the argument is, pull data from one of two possible public APIs, perform some transformations on them, and them write the results to an in-memory SQLite database. One of the data sources should be handled as a Polars dataframe, but the other can processed however you see fit. 

Be generous with comments about the functional programming implementation.

There should be multiple python modules with names corresponding to the action they perform (not just `data`, `calculations`, and `actions`). There should be a clear delineation of core functional / pure methods and imperative, shell / impure methods. 