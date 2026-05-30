# Karena AI — Technical Cost Modeling for APAC Deployments

## Executive Summary

This document provides granular infrastructure expenditure modeling for Karena AI deployments across Asia-Pacific enterprise environments, decomposing total cost of ownership across compute, storage, networking, and AI inference components under low, medium, and high utilization regimes. The modeling incorporates Google Cloud's sustained use discounts, committed use contracts, and preemptible VM pricing strategies to optimize operational expenditure while preserving performance service level agreements. Sensitivity analysis demonstrates how variations in query volume, embedding dimensionality, cache hit rates, and model selection impact monthly expenditure, enabling data-driven architectural decisions that balance capability with fiscal responsibility across diverse APAC enterprise budgets.

## Cost Component Decomposition

### Compute Infrastructure Costs

Compute costs constitute the largest variable expenditure component driven by query processing demands embedding generation latency requirements and LLM inference workloads. Base application tier running FastAPI services requires modest compute resources with two vCPU eight GB memory instances sufficient handle thousands concurrent requests when properly cached. Embedding generation represents compute-intensive operation requiring GPU acceleration production environments where sub-second response mandates pre-computed embeddings batch processing workloads.

Low utilization scenario assumes ten thousand queries daily averaging point three queries per second with burst capacity hundred queries per minute. Compute configuration utilizes two application instances n2-standard-2 pricing approximately fifty dollars monthly per instance on-demand or thirty-five dollars monthly with committed use discounts. Embedding workload processes batch during off-peak hours utilizing preemptible T4 GPU instances reducing embedding compute costs seventy percent compared on-demand pricing. Total monthly compute expenditure low utilization approximates one hundred fifty dollars on-demand or one hundred dollars committed use blended pricing.

Medium utilization scenario assumes one hundred thousand queries daily averaging three queries per second peak twelve queries per second business hours. Compute configuration scales eight application instances n2-standard-4 handling increased concurrency maintaining latency targets. Dedicated embedding service utilizes T4 GPU instances running continuously rather preemptible ensuring availability real-time document ingestion. LLM inference leverages cloud AI endpoints paying per-token basis estimated two thousand dollars monthly based average query complexity response lengths. Total monthly compute expenditure medium utilization approximates four thousand dollars on-demand or two thousand eight hundred dollars optimized committed use blending.

High utilization scenario assumes one million queries daily averaging thirty queries per second peak hundred twenty queries per second. Compute configuration deploys thirty-two application instances n2-standard-8 distributed multiple zones high availability. Embedding service utilizes V100 A100 GPU clusters handling continuous ingestion real-time embedding updates. LLM inference implements model routing directing simple queries distilled models complex queries full-capability models optimizing cost-quality trade-offs. Dedicated autoscaling policies add capacity traffic spikes remove underutilized resources idle periods. Total monthly compute expenditure high utilization approximates twenty-five thousand dollars on-demand or seventeen thousand five hundred dollars optimized contracting.

### Storage Infrastructure Costs

Storage costs encompass vector database persistence conversation memory archives audit log retention backup snapshots disaster recovery replicas. Vector storage dominates expenditure proportional corpus size embedding dimensionality retention policies. Qdrant storage efficiency achieves approximately one hundred vectors per megabyte three hundred eighty-four dimensional embeddings compressed HNSW index structures.

Low utilization scenario maintains one million document corpus requiring approximately ten gigabytes vector storage plus metadata overhead totaling fifteen gigabytes. SSD persistent disk pricing ten cents GB monthly yields one hundred fifty dollars vector storage. Conversation memory stores thirty-day retention approximately five gigabytes SQL database costing fifty dollars monthly. Audit logs retain ninety days compliance requirements adding two gigabytes costing twenty dollars. Backup snapshots replicate data secondary region disaster recovery doubling storage costs. Total monthly storage expenditure low utilization approximates four hundred forty dollars.

Medium utilization scenario maintains ten million document corpus requiring one hundred fifty gigabytes vector storage plus metadata totaling two hundred twenty-five gigabytes costing two thousand two hundred fifty dollars monthly. Conversation memory expands fifty gigabytes accommodating more users longer retention costing five hundred dollars. Audit logs expand twenty gigabytes comprehensive compliance tracking costing two hundred dollars. Multi-region replication disaster recovery adds one thousand dollars. Total monthly storage expenditure medium utilization approximates three thousand nine hundred fifty dollars.

High utilization scenario maintains one hundred million document corpus requiring one point five terabytes vector storage plus metadata totaling two point two terabytes costing twenty-two thousand dollars monthly. Conversation memory expands five hundred gigabytes global user base costing five thousand dollars. Comprehensive audit logging retains one year regulatory requirements two hundred gigabytes costing two thousand dollars. Multi-region active-active replication triples storage costs adding twenty-nine thousand dollars. Total monthly storage expenditure high utilization approximates fifty-eight thousand dollars.

### Networking Infrastructure Costs

Networking costs include inter-service communication cross-zone traffic egress charges content delivery distribution API gateway data transfer. Intra-region traffic typically free major cloud providers while cross-region replication incurs egress charges. Content delivery network caching reduces origin server load improving response times geographically distributed users.

Low utilization scenario minimal cross-region traffic primarily single-region deployment. CDN caching static assets costs fifty dollars monthly serving regional users. API gateway data transfer negligible within free tier. Total monthly networking expenditure low utilization approximates fifty dollars.

Medium utilization scenario implements multi-region active-passive failover Singapore primary Sydney secondary. Cross-region replication generates five hundred GB monthly egress costing sixty dollars. CDN distributes content APAC regions costing two hundred dollars monthly. API gateway processes significant throughput incurring five hundred dollars data transfer fees. Total monthly networking expenditure medium utilization approximates eight hundred ten dollars.

High utilization scenario deploys multi-region active-active across Singapore Tokyo Sydney minimizing latency regional users. Cross-region synchronization generates five TB monthly egress costing six hundred dollars. Global CDN distribution costs one thousand five hundred dollars monthly. API gateway high throughput incurs five thousand dollars data transfer. DDoS protection premium tier adds five hundred dollars. Total monthly networking expenditure high utilization approximates seven thousand six hundred dollars.

### AI Inference Costs

AI inference costs vary dramatically based model selection query complexity usage patterns routing strategies. Embedding inference relatively inexpensive once models loaded memory while LLM generation dominates inference expenditure proportional token counts.

Low utilization scenario utilizes mock LLM responses development testing minimal production inference costs. Embedding model runs locally no additional inference charges. Total monthly AI inference expenditure low utilization approximates zero dollars self-hosted models.

Medium utilization scenario implements hybrid approach simple queries utilize cached responses or small distilled models complex queries full-capability models. Average query consumes five hundred input tokens two hundred output tokens pricing approximately point zero zero two dollars per query. One hundred thousand daily queries yield six thousand dollars monthly inference costs. Caching achieves sixty percent hit rate reducing effective inference costs two thousand four hundred dollars. Total monthly AI inference expenditure medium utilization approximates two thousand four hundred dollars optimized caching.

High utilization scenario implements sophisticated model routing eighty percent queries handled distilled models costing point zero zero zero five dollars per query twenty percent complex queries full models costing point zero one dollars per query. One million daily queries yield blended cost per query point zero zero two four dollars totaling twenty-four thousand dollars monthly. Advanced caching ninety percent hit rate reduces effective costs two thousand four hundred dollars. Quantization techniques further reduce costs thirty percent. Total monthly AI inference expenditure high utilization approximates one thousand six hundred eighty dollars highly optimized.

## Total Cost of Ownership Summary

| Utilization Level | Compute | Storage | Networking | AI Inference | Total Monthly |
|-------------------|---------|---------|------------|--------------|---------------|
| Low (10K queries/day) | $100 | $440 | $50 | $0 | $590 |
| Medium (100K queries/day) | $2,800 | $3,950 | $810 | $2,400 | $9,960 |
| High (1M queries/day) | $17,500 | $58,000 | $7,600 | $1,680 | $84,780 |

*Note: Costs reflect optimized configurations with committed use discounts caching optimization and model routing. On-demand pricing without optimization may exceed these estimates fifty to one hundred percent.*

## Sensitivity Analysis

### Query Volume Sensitivity

Query volume directly impacts compute AI inference networking costs while storage remains relatively fixed determined corpus size rather query count. Doubling query volume approximately doubles compute inference costs assuming constant cache hit rates. Improving cache hit rates from sixty percent ninety percent reduces inference costs sixty-seven percent providing significant ROI caching optimization investments.

### Embedding Dimensionality Sensitivity

Embedding dimensionality affects storage compute proportionally. Three hundred eighty-four dimensional embeddings require half storage seven hundred sixty-eight dimensional embeddings while five hundred twelve dimensional embeddings offer middle ground. Higher dimensions may improve retrieval quality justifying increased costs domains requiring precision. Lower dimensions suffice general knowledge domains reducing storage compute costs proportionally.

### Cache Hit Rate Sensitivity

Cache hit rate represents highest-leverage optimization knob available operations teams. Improving cache hit rate from sixty percent ninety percent reduces inference costs sixty-seven percent while improving response latencies eliminated inference overhead entirely cached queries. Cache warming predictive pre-fetching strategies achieve ninety percent hit rates common query patterns yielding substantial cost savings.

### Model Selection Sensitivity

Model selection creates order-of-magnitude cost variations. Large LLMs cost ten times more per query than distilled models while providing marginal quality improvements routine queries. Intelligent routing ninety percent queries small models ten percent complex queries large models achieves ninety percent cost savings versus all-large-model approach while maintaining quality user-facing metrics.

## Optimization Levers and Fiscal Governance

Committed-use commitments baseline capacity realize twenty-five thirty percent savings versus on-demand pricing. Preemptible spot VMs batch embedding retraining workloads reduce compute costs seventy percent interruptible workloads. Multi-tier caching embedding quantization reduce storage compute requirements significantly. Model routing small models routine queries large models high-value interactions optimizes cost-quality trade-offs. Regional compute placement minimizes egress costs data residency compliance.

Continuous cost telemetry tracks per-query cost per-corpus storage cost cache effectiveness enabling data-driven optimization. Monthly budget reviews tie usage forecasts actual expenditure identifying variance root causes corrective actions. Alerting thresholds notify teams expenditure anomalies preventing budget overruns. FinOps practices institutionalize cost accountability engineering decisions balancing capability fiscal responsibility.

## Comparative Cost-Benefit Analysis

Self-hosted vector databases versus managed Qdrant reveals trade-offs control cost operational overhead. Self-hosting reduces direct costs thirty percent requires dedicated operations staff monitoring maintenance patching increasing total cost labor. Managed services provide operational excellence automated backups scaling patches justifying premium organizations prioritizing engineering focus core competencies.

Third-party RAG platforms versus custom Karena AI implementation shows build-buy considerations. Third-party platforms accelerate time-market months reduce development risk charge premium per-query pricing making expensive scale. Custom implementation requires upfront development investment yields lower marginal costs scale providing ROI twelve eighteen months moderate-high utilization scenarios.

Hybrid approaches leverage third-party platforms proof-of-concept validation migrate custom implementations production realizing best both worlds rapid validation long-term cost efficiency. Karena AI architecture supports migration paths enabling organizations start managed services transition self-hosted components maturity scale justify investment.
