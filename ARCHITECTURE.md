# Sentinel Architecture Notes

This document describes the current architecture of the Sentinel platform, specifically contrasting the current implementation with a production-grade streaming architecture.

## Current Architecture (Hackathon Prototype)

The current platform is built for ease of deployment, rapid iteration, and demonstrating the core Machine Learning pipelines.

### 1. Dashboard Real-Time Updates
- **Implementation**: The React frontend (`App.tsx`) uses a **lightweight polling mechanism**.
- **How it works**: The dashboard makes a synchronous REST API call (via `fetchDashboardData`) every 30 seconds to fetch the latest aggregate stats, trends, and alerts from the backend.
- **Why**: This avoids the complexity of standing up a dedicated WebSocket/SSE server or message broker for the hackathon, ensuring stable and reliable demonstrations.

### 2. ML Inference Pipeline
- **Implementation**: Real-time single-record inference is exposed via a synchronous `POST /predict` FastAPI endpoint.
- **How it works**: An external system (or a simulated script) sends a JSON payload representing a single access log. The FastAPI server runs the Isolation Forest, Random Forest, and SHAP explainability inline, and returns the result in the same HTTP response.

## Production Streaming Architecture (Future State)

To scale Sentinel to ingest tens of thousands of logs per second in a real-world enterprise environment, the architecture would need to evolve from synchronous REST to asynchronous event streaming.

### 1. True Real-Time Ingestion (Message Queues)
Instead of a `POST /predict` endpoint, raw logs would be ingested directly into a high-throughput message broker like **Apache Kafka** or **AWS Kinesis**. This decouples ingestion from processing, ensuring that sudden spikes in network traffic do not overwhelm the ML inference servers.

### 2. Stream Processing (Flink / Spark)
The ML inference engine would be deployed as consumers of the Kafka topic, potentially using a stream processing framework like **Apache Flink** or **Spark Streaming**. This allows for horizontally scaling the ML workers independent of the web server.

### 3. Push-Based Dashboard Updates (WebSockets / SSE)
Instead of the frontend polling every 30 seconds, the backend would maintain an active **WebSocket** or **Server-Sent Events (SSE)** connection with the client. When a new alert is classified by the ML consumers, it is written to the database (e.g., Firestore) and immediately pushed to all connected clients with zero latency.
