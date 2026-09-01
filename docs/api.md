# API Reference

Generated reference for the RepeaterBook Python Client.

Rendering options are configured globally in `mkdocs.yml`, so each section below
just names the module it documents.

## Package exports

The names re-exported at the top level: the `Repeater` model, the `RepeaterBook`
database handle, and the exception hierarchy. Everything else is imported from
its own module.

::: repeaterbook

## Models

The `Repeater` ORM row, the API's JSON `TypedDict`s, and `ExportQuery`.

::: repeaterbook.models

## Services

The API client, HTTP caching, endpoint routing, and JSON → model conversion.

::: repeaterbook.services

## Database

SQLite persistence.

::: repeaterbook.database

## Queries

Composable filter builders and the radius search.

::: repeaterbook.queries

## Spec

`RepeaterSpec`, the neutral output contract, and its JSON Schema.

::: repeaterbook.spec

## Utils

Geographic types and the constrained numeric aliases used across the contract.

::: repeaterbook.utils

## Exceptions

::: repeaterbook.exceptions

## North American state IDs

RepeaterBook's own `state_id` vocabulary for the US, Canada and Mexico.

::: repeaterbook.na_states

## CSV export

Reads RepeaterBook's CSV export format into `Repeater` rows.

::: repeaterbook.csv_export
