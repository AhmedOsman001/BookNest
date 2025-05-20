# Elasticsearch Integration for BookNest

This document provides information about the Elasticsearch integration in the BookNest application.

## Overview

Elasticsearch has been integrated into BookNest to provide powerful search capabilities for books. The integration includes:

- Full-text search across book titles, authors, descriptions, and other fields
- Search suggestions as users type (autocomplete)
- Fuzzy matching to handle typos and spelling variations
- Relevance-based ranking of search results

## Setup Instructions

### 1. Install Elasticsearch

First, you need to install Elasticsearch 7.x. You can download it from the [official website](https://www.elastic.co/downloads/past-releases/elasticsearch-7-17-9) or use Docker:

```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.9
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.17.9
```

### 2. Install Required Python Packages

The required packages have been added to `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

### 3. Create and Populate the Index

Use the provided management command to create and populate the Elasticsearch index:

```bash
python manage.py rebuild_search_index
```

## Usage

### Search API

The search API endpoint now uses Elasticsearch as the primary search method, with fallbacks to the database and external APIs:

```
GET /api/v1/books/search/?q=your_search_query
```

### Suggestions API

A new suggestions API endpoint has been added to provide autocomplete functionality:

```
GET /api/v1/books/suggestions/?q=partial_query&limit=5
```

## Implementation Details

### Search Flow

1. When a search query is received, the system first searches in Elasticsearch
2. If no results are found in Elasticsearch, it falls back to the database
3. If still no results, it searches external APIs (OpenLibrary and Google Books)

### Document Structure

The Elasticsearch document for books includes:

- Basic book information (ISBN, title, description, etc.)
- Nested fields for authors
- Keyword fields for genres
- Completion suggester for autocomplete functionality

### Indexing

Books are automatically indexed in Elasticsearch when they are created or updated. You can also manually rebuild the index using the management command mentioned above.

## Troubleshooting

- If search is not working, ensure Elasticsearch is running: `curl http://localhost:9200`
- Check the logs for any Elasticsearch connection errors
- Verify that the index exists: `curl http://localhost:9200/_cat/indices`
- Rebuild the index if necessary: `python manage.py rebuild_search_index`