# All Spring AI Issues with `design` Label


## 🧵 Issue #3103: Add Model Captability class

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/3103)


**Summary:**  
Both #2787  and #2863 would benefit from having a Model Capability class that describes what functionality the model supports.   
  
For the case of the reasoning models, this capability would enable one to copy the current systemMessage into a 'developerMessage' (as required by the `o` series of openai models) and for structured output one can switch to use the JSON mode vs. the current strategy of adding to the prompt the 'please convert my json` message.  
  
There is a wide range of features that fall under this umbrella, so a good design is need. Multimodality is another one, we can proactively know that a request with Media would not be supported by a given model.


## 🧵 Issue #2104: Add an opportunity to choose a model in vector store

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/2104)


**Summary:**  
**Expected Behavior**  
  
```  
	void add(List<Document> documents, String model);  
	@Nullable  
	List<Document> similaritySearch(SearchRequest request, String model);  
```  
or  
```  
	void add(List<Document> documents, EmbeddingOptions options);  
	@Nullable  
	List<Document> similaritySearch(SearchRequest request, EmbeddingOptions options);  
```  
  
  
**Current Behavior**  
Currently there is no opportunity to send requests providing different models. But in chatClient it is possible.  
  
**Context**  
Currently I use a weird decorator in order to support different models for different clients, which includes a lot of boilerplate code to make it compatible with my specific vector store. I've seen some issues about redesigning of the vector store to separate logic of calling embedding model and saving documents. Are there some plans to do it this way? Would be lovely.. Thanks in advance


## 🧵 Issue #1838: Are `Document` objects supposed to be immutable?

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1838)


**Summary:**  
The `Document` class contains only final fields (except "embeddings" which is about to be removed). However, the `media` (collection) and `metadata` (map) are mutable. All vector store implementations, at least, rely on the `metadata` field to be mutable because they add new metadata.  
  
https://github.com/spring-projects/spring-ai/pull/1794 introduced a `mutate()` method to build new instances of `Document` objects. This issue is to discuss whether `Document` should be immutable. If yes, we need to to refactor all vector store implementations to work accordingly. Also, it's a breaking change, so it should be documented and communicated in the release notes.


## 🧵 Issue #1815: About Chat Memory’s message management strategy and other storage implementations

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1815)


**Summary:**  
Hi community,   
  
I would like to ask, regarding Chat Memory, is the community ready to implement some other storage methods, such as Mysql, redis, etc.  
  
Is there any message management strategy similar to Langchain4j's TokenWindow and TimeWindow for Message?  
  
Thank you so much!


## 🧵 Issue #1775: milvus vectorstore SearchRequest  Cannot specify database

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1775)


**Summary:**  
![image](https://github.com/user-attachments/assets/4e7a17cb-2bab-4a7b-bfe1-76e542946fa3)


## 🧵 Issue #1758: Improve Spring AI Bedrock Converse API Integration

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1758)


**Summary:**  
Extend the [Spring AI Bedrock Converse](https://docs.spring.io/spring-ai/reference/api/bedrock-converse.html) integration with support for the following Bedrock [Converse](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html) and [ConverseStream](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ConverseStream.html) API features:  
  
- [ ] [additionalModelRequestFields](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax) - Additional inference parameters that the model supports, beyond the base set of inference parameters that Converse and ConverseStream support in the inferenceConfig field.  
- [ ] [ConverseMetrics](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ConverseMetrics.html) and [ConverseStreamMetrics](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ConverseStreamMetrics.html) - Metrics for a call to Converse and ConverseStream  
- [ ] [Guardrail](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailConfiguration.html), [Include a guardrail with Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html) - Guard conversational apps that you create with the Converse  
- [ ] Provider better control over the built-in API retry configuration capabilities.


## 🧵 Issue #1704: Provider Exception Failure Analysis abstraction to provide better error messages to users

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1704)


**Summary:**  
Since Spring AI integrates with numerous vector stores and models Exceptions are going to happen and users will struggle to figure out why the exception is occurring. Sprig Boot has the concept of [Exception failure analyzer]( https://docs.spring.io/spring-boot/api/java/org/springframework/boot/diagnostics/AbstractFailureAnalyzer.html) by introducing a failure analyzer abstraction into the spring-ai core we can enable model providers, vector store providers and advisor implementers the ability to offer more friendly error messages that will guide users towards a quick resolution of the issues and reduce the volume of Q&A issues raised.  
  
Examples of users raising issues that can benefit from a failure analyzer.   
- #1675


## 🧵 Issue #1629: Support dynamic API keys / paltform based workload identity systems 

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1629)


**Summary:**  
Epic to track issues related to using spring-ai against providers that issue short lived api keys, or offer platform based identity frameworks that enable keyless authentication.   
  
- #1387   
- #1626   
- #1624


## 🧵 Issue #1611: Health indicators for vector stores (and any other external APIs)

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1611)


**Summary:**  
Given that vector stores are databases that are external to the application, which could go down or otherwise become unavailable, and as such contribute to the health (or lack thereof) of a Spring AI application...  
  
It would be great if Spring AI provided health indicators for the vector stores that contribute to Actuator's health endpoint.  
  
One question concerning this is whether such health indicators would be needed for vector stores that are also databases for which Spring already has health indicators. For example, Postgres and Mongo probably are already covered by health indicators. But things like Chroma and Milvus probably aren't.


## 🧵 Issue #1600: VectorStore improvements.

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1600)


**Summary:**  
Current vectorstore interface is lacking in two important areas  
  
* Does not support other types of search other than similarity search  
* Does not support full api coverate for admin cases, e.g. delete, update operations


## 🧵 Issue #1594: Consider using a builder class for creating Messages

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1594)


**Summary:**  
See https://github.com/spring-projects/spring-ai/pull/427 and related issue https://github.com/spring-projects/spring-ai/issues/1592


## 🧵 Issue #1582: Enhancing the architecture of the ETL pipeline's transformers

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1582)


**Summary:**  
When building an ETL pipeline, transformers may need to perform multiple actions, which can result in layers of function calls that are hard to maintain. Is it possible to design them like advisor ?  
  
  
The following actions include chunking, keyword, and summarization. If more transformations are required in the future, additional layers will need to be added.  
  
`vectorStore.write(splitter.split(loadTextAsDocuments( summaryDocuments(keywordDocuments(docs))));`


## 🧵 Issue #1563: Support multimodality in chat completion output

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1563)


**Summary:**  
OpenAI has recently introduced audio multimodality support, both for input and output.   
  
The input audio modality support is introduced in https://github.com/spring-projects/spring-ai/issues/1560 all the way up to the Spring AI abstractions.  
  
The output audio modality is only supported at the lower level (`OpenAIApi`). Its usage is demonstrated in this integration test: https://github.com/spring-projects/spring-ai/blob/bdb66e5770836dc9dec6be40af801d9cd9e41e2a/models/spring-ai-openai/src/test/java/org/springframework/ai/openai/api/OpenAiApiIT.java#L98-L118  
  
It would be nice to start identifying what type of abstractions are needed in the `ChatResponse` API to include audio response data.


## 🧵 Issue #1562: Review the Media APIs for multimodality

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1562)


**Summary:**  
The current `Media` API provides a generic way of adding multimedia content to a prompt when calling models with multimodality support.  
  
So far, the `Media` API has been used for images. Starting with https://github.com/spring-projects/spring-ai/issues/1560, it's also used for audio files. It's working correctly, but there are two points that might be improved:  
  
1. The `MimeTypeUtils` from Spring Framework doesn't include any audio-related mime types. Therefore, developers need to use an explicit one, such as `MimeTypeUtils.parseMimeType("audio/mp3")`. Perhaps we can introduce an audio-specific utility in Spring AI?  
  
2. When the media content is extracted from the Spring AI `UserMessage` into the provider-specific APIs (such as OpenAI), there's no immediate way to filter the media content based on whether it's image or audio content. For now, support only exists in the OpenAI integration and the audio content is checked individually (see: https://github.com/spring-projects/spring-ai/pull/1561), where there's also the additional challenge of mapping mime type to an OpenAI-specific enum. There might be room for streamlining this logic.


## 🧵 Issue #1478: Introduce TranscriptionModel interface

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1478)


**Summary:**  
Even though only OpenAI and Azure OpenAI current offer transcription support, they are each represented by distinct transcription model types: `OpenAiAudioTranscriptionModel` and `AzureOpenAiAudioTranscriptionModel`. There is no common interface between these two, which means that you have to explicitly inject the one you are working with rather than inject a common interface.  
  
They both implement `Model<AudioTranscriptionPrompt, AudioTranscriptionResponse>`, but it would be more handy to have a common interface like this that they each could implement:  
  
```  
public interface TranscriptionModel extends Model<AudioTranscriptionPrompt, AudioTranscriptionResponse> {  
  
  AudioTranscriptionResponse call(AudioTranscriptionPrompt transcriptionPrompt);  
  
}  
```  
  
Similar to `ChatModel`, there may be opportunity for some additional default convenience methods, as well. Perhaps one that accepts a `Resource` and returns a `String` and another that accepts a `Resource` and `AudioTranscriptionOptions` and produces a `String`.


## 🧵 Issue #1439: Optimized aggregation advisors for streaming scenarios

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1439)


**Summary:**  
In the latest round of architectural changes of Advisors in #1422 there now are two types of advisors:  
* `CallAroundAdvisor`  
* `StreamAroundAdvisor`  
  
In the case of the non-streaming one, it's easy to take some actions based on the entire response. However, the streaming manipulates an entire stream. A next advisor in the chain can also manipulate the entire stream. If a stream advisor in the middle is acting upon each chunk of the response, all should be fine. However, if the advisor is only interested in the entire aggregation it would modify the stream in a way that aggregates everything in a side channel, e.g. using `org.springframework.ai.chat.model.MessageAggregator` class. If multiple advisors perform the same type of aggregation it is inefficient in terms of both time and memory.  
  
Having that, I propose a new interface, `StreamAggregationAdvisor`. Instances of this type would be fed with an aggregation of the original stream of chunks coming back from the model on their way into the application before any other advisors have a chance to manipulate the stream. The aggregation would then be performed once and could deal with the unaltered view of the exchange. The way to implement this behaviour would be based on utilizing the innermost `StreamAroundAdvisor` that is created in the `DefaultChatClient`.


## 🧵 Issue #1291: Use @NonNull annotations for parameters and return types

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1291)


**Summary:**  
Using Spring AI from Kotlin, it's noticeable that unlike Spring Framework, it doesn't use `@NonNull` annotations, which are appropriate for most parameters and return types.   
  
Doing this would not  only make Spring AI nicer to use from Kotlin, but make the Java code clearer and more consistent with other Spring projects.


## 🧵 Issue #1257: Investigate supporting the use case of retrieving multi-modal documents

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1257)


**Summary:**  
**Bug description**  
创建 Document 时 ，嵌入了 Media 对象，但通过 vectorStore.similaritySearch 查询后，返回的 document 中 Media Collection 为空  
  
**Environment**  
Please provide as many details as possible: Spring AI version, Java version, which vector store you use if any, etc  
Springboot 3.3.2  
SpringAI 1.0.0.SNAPSHOT  
Java 17  
Chroma   
  
**Steps to reproduce**  
1. 使用 Document doc = new Document(docId, docContent, mediaList, metadata); 新建 doc 并 调用 vectorStore.add(doc); 插入向量库  
2. 使用 List<Document> docs = vectorStore.similaritySearch(SearchRequest.defaults().withTopK(1)..withFilterExpression(filterExpr).withQuery(query)); 查询结果  
3. 确认 docs 中包含 与 doc 相同ID 的元素，但元素中的 media 为空  
4. 跟踪进入 org.springframework.ai.vectorstore.ChromaVectorStore 类的 similaritySearch 方法中，发现在处理查询结果时，没有使用带 media 的构造函数  
5. VectorStore 接口中没有提供其他方法能 获取 与 Document 管理的 Media 集合  
  
**Expected behavior**  
希望使用 vectorStore.similaritySearch 查询时，能同时带出所关联的 media 集合，否则这 media 集合就没有意义了  
  
**Minimal Complete Reproducible example**  
请见重现步骤部分


## 🧵 Issue #1193: Add proper retry implementation for OpenAiChatModel streaming

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/1193)


**Summary:**  
Blocking calls use RetryTemplate, however there isn't equivalent functionality for the streaming use cases.


## 🧵 Issue #982: milvus multiple vector fields  in the same collection

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/982)


**Summary:**  
support milvus multiple vector fields  in the same collection  and  hybrid search


## 🧵 Issue #557: Feature Request : Consider making the ImageOptions properties such as N, Quality, dimensions etc to be an enum

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/557)


**Summary:**  
Consider making the ImageOptions properties such as N, Quality, dimensions etc to be an enum. For example, OpenAiImageOptions quality could be of two types, standard & hd. So if the well known property values are made as enum, it would help the devs and avoid them making wrong calls. For example, I was not aware of the standard type, so having seen hd, I supplied sd, thinking standard definition i.e. sd, would be supported, however this wasn't the case and I lost a few tokens in this call. Likewise, I lost quite a few iterations for the dimensions as well. With this kind of use case, please do consider making these kind of properties to be enum while retaining the current string type support (this will help with future extensibility, where a new feature introduced by any LLM could be supplied as String till the time the enum isn't updated). Thanks!


## 🧵 Issue #517: Add advanced RAG (Hybrid Search and Semantic Hybrid Search) with Azure AI Search

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/517)


**Summary:**  
Azure AI Search has the following feature along with Vector Similarity Search (which is already present in Spring AI).  
  
- Hybrid Search (Vector Search + Text Search)  
- Semantic Hybrid Search (Hybrid search + re-ranking)  
  
In the JavaScript Langchain [project](https://github.com/langchain-ai/langchainjs/blob/main/libs/langchain-community/src/vectorstores/azure_aisearch.ts) they basically have the 3 search models in 3 functions next to each other:  
  
1. similaritySearchVectorWithScore - this is the current vector search Spring AI already has  
2. hybridSearchVectorWithScore - this is vector search + text search  
3. semanticHybridSearchVectorWithScore - this is hybrid search + reranking  
  
I see something similar was recently introduced in the Langchain4j project too. Would be good to have this feature in Spring AI as well.


## 🧵 Issue #512: HTTP Client configuration for models and vector stores

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/512)


**Summary:**  
### Enhancement Description  
  
Each model integration is composed of two aspects: an `*Api` class calling the model provider over HTTP, and a `*Client` class encapsulating the LLM specific aspects.  
  
Each `*Client` class is highly customizable based on nice interfaces, making it possible to overwrite many different options. It would be nice to provide similar flexibility for each `*Api` class as well. In particular, it would be useful to be able to configure options related to the HTTP Client.  
  
Examples of aspects that would need to be configured:  
  
* enable logging of requests/responses, very useful for general troubleshooting but also for refining prompts during development and testing;  
* define connection and read timeout settings;  
* configure an `SslBundle` to connect with on-prem model providers using custom CA certificates;  
* configure connections through a corporate proxy, very common in production deployments.  
  
Furthermore, there might be additional needs for configuring resilience patterns:  
  
* configure retry strategy in case of failures;  
* define a fallback logic in case of failures.  
  
More settings that right now are part of the model connection configuration (and that still relates to the HTTP interaction) would also need to be customisable in enterprise use cases in production (e.g. multi-user applications or even multi-tenant applications). For example, when using OpenAI, the following could need changing per request/session.  
  
* API Key  
* Organization  
* User  
  
All the above is focused on the HTTP interactions with model providers, but the same would be useful for vector stores.  
  
### Possible Solutions  
  
Drawing from the nice abstractions designed to customize the model integrations and ultimately implementing the `ModelOptions` interface, it could be an idea to define a dedicated abstraction to pass HTTP client customizations to an `*Api` class (something like `HttpClientConfig`), which might also be exposed via configuration properties (under `spring.ai.<model>.client.*`).  
  
For the more specific resilience configurations (like retries and fallbacks), an annotation-driven approach might be more suitable. Resilience4j might provide a way to achieve this, since I don't think Spring supports the Fault Tolerance Microprofile spec.  
  
A partial alternative solution would be for developers to define a custom `RestClient.Builder` or `WebClient.Builder` and pass that to each `*Api` class, but it would result in a lot of extra configurations and reduce the convenience of the autoconfiguration. Also, it would tight a generic configuration like "enable logs" or "use a custom CA" to the specific client used, resulting in duplication when both blocking and streaming interactions are used in the same application.  
  
I'm available to contribute and help solve this issue.  
  
### Related Issues  
  
* https://github.com/spring-projects/spring-ai/issues/123  
* https://github.com/spring-projects/spring-ai/issues/354  
* https://github.com/spring-projects/spring-ai/issues/441  
* https://github.com/spring-projects/spring-ai/issues/477


## 🧵 Issue #468: Support Vector Databases  Multiple indexes or collections

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/468)


**Summary:**  
## Expected Behavior  
  
I would like to be able to support multiple indexes or collections for vector data instead of being limited to configuring just one index. For example, in Redis or Qdrant implementations, it would be beneficial to have the ability to add vectors to different collections or indexes based on the business requirements.  
  
An example method signature could be:  
  
 ```  
void add(List<Document> documents, String collectionName);  
```  
  
## Current Behavior  
  
https://github.com/spring-projects/spring-ai/blob/7634c6b78087a708a1dff8592b1485806da8ed4d/spring-ai-core/src/main/java/org/springframework/ai/vectorstore/VectorStore.java#L32-L73  
  
  
Currently, the system only allows for configuring a single index or collection for storing vector data. This limitation restricts the flexibility and scalability of the system, especially when there is a need to store vectors in multiple separate collections or indexes.  
  
## Context  
  
This feature request is essential for scenarios where there is a requirement to store and retrieve vector data from different collections or indexes based on specific use cases or business logic. Without the ability to support multiple indexes or collections, the current system falls short in meeting the diverse needs of various applications that rely on vector data storage.  
  
I have considered the workaround of creating separate instances of the vector storage system for each collection needed, but this approach is not scalable and creates unnecessary complexity in managing multiple instances.  
  
Having an add method that supports specifying the collection name or index where the documents should be added would greatly enhance the flexibility and usability of the system.


## 🧵 Issue #431: Add the low-level message ID and finishReason to SpringAI's Message properties. 

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/431)


**Summary:**  
For example the Generation currently contains the finishReason but doesn't propagate ID to the Message.


## 🧵 Issue #372: 'JsonEOFException: Unexpected end-of-input: expected close marker for Object' when making synchronous openAiChatClient.call

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/372)


**Summary:**  
**Bug description**  
When making a basic synchronous openAiChatClient.call( prompt) with a single UserMessage, an Exception is thrown (com.fasterxml.jackson.core.io.JsonEOFException: Unexpected end-of-input: expected close marker for Object (start marker at [Source: (org.springframework.util.StreamUtils$NonClosingInputStream); line: 1, column: 1]))  
  
I have inspected the traffic using Charles, and the OpenAI API is returning a correct JSON response.   
  
**Environment**  
Please provide as many details as possible: Spring AI version, Java version, which vector store you use if any, etc  
OpenJDK 18.0.2  
Spring Framework 6.1.4  
Spring Boot 3.2.3  
Spring Open AI 0.8.0-SNAPSHOT  
  
**Steps to reproduce**  
Basic synchronous call   
  
```  
String message = "Tell me about OpenAI";  
UserMessage userMessage = new UserMessage( message );  
List<Message> openAiMessages = List.of( userMessage );  
Prompt prompt = new Prompt( openAiMessages );  
ChatResponse call = openAiChatClient.call( prompt );  
Generation generation = call.getResults().get( 0 );  
System.out.println( generation.getOutput().getContent() );  
```  
  
**Expected behavior**  
Chat response is printed.  
  
**Stack Trace**  
```  
Caused by: org.springframework.http.converter.HttpMessageNotReadableException: JSON parse error: Unexpected end-of-input: expected close marker for Object (start marker at [Source: (org.springframework.util.StreamUtils$NonClosingInputStream); line: 1, column: 1])  
  at org.springframework.http.converter.json.AbstractJackson2HttpMessageConverter.readJavaType(AbstractJackson2HttpMessageConverter.java:406) ~[spring-web-6.1.4.jar:6.1.4]  
	at org.springframework.http.converter.json.AbstractJackson2HttpMessageConverter.read(AbstractJackson2HttpMessageConverter.java:354) ~[spring-web-6.1.4.jar:6.1.4]  
	at org.springframework.web.client.DefaultRestClient.readWithMessageConverters(DefaultRestClient.java:213) ~[spring-web-6.1.4.jar:6.1.4]  
	... 82 common frames omitted  
Caused by: com.fasterxml.jackson.core.io.JsonEOFException: Unexpected end-of-input: expected close marker for Object (start marker at [Source: (org.springframework.util.StreamUtils$NonClosingInputStream); line: 1, column: 1])  
 at [Source: (org.springframework.util.StreamUtils$NonClosingInputStream); line: 1, column: 2]  
	at com.fasterxml.jackson.core.base.ParserMinimalBase._reportInvalidEOF(ParserMinimalBase.java:697) ~[jackson-core-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.core.base.ParserBase._handleEOF(ParserBase.java:512) ~[jackson-core-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.core.base.ParserBase._eofAsNextChar(ParserBase.java:529) ~[jackson-core-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.core.json.UTF8StreamJsonParser._skipWSOrEnd(UTF8StreamJsonParser.java:3103) ~[jackson-core-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.core.json.UTF8StreamJsonParser.nextToken(UTF8StreamJsonParser.java:757) ~[jackson-core-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.databind.deser.BeanDeserializer.deserialize(BeanDeserializer.java:181) ~[jackson-databind-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.databind.deser.DefaultDeserializationContext.readRootValue(DefaultDeserializationContext.java:323) ~[jackson-databind-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.databind.ObjectReader._bindAndClose(ObjectReader.java:2105) ~[jackson-databind-2.15.4.jar:2.15.4]  
	at com.fasterxml.jackson.databind.ObjectReader.readValue(ObjectReader.java:1481) ~[jackson-databind-2.15.4.jar:2.15.4]  
	at org.springframework.http.converter.json.AbstractJackson2HttpMessageConverter.readJavaType(AbstractJackson2HttpMessageConverter.java:395) ~[spring-web-6.1.4.jar:6.1.4]  
	... 84 common frames omitted  
```


## 🧵 Issue #328: Add 'like' operator in FilterExpressionBuilder

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/328)


**Summary:**  
**Expected Behavior**  
  
The document of FilterExpressionBuilder says "This builder DSL mimics the common https://www.baeldung.com/hibernate-criteria-queries syntax." I'd expect all common hibernate operators supported, but the 'like' operator is not supported here.  
  
**Current Behavior**  
  
No 'like' operator so you can't filter by a metadata containing a certain string.  
  
**Context**  
  
Many times the similarity search can't return the desired results as the algorithm does not work like the traditional deterministic comparison, in that case we could combine the traditional search against metadata to improve the results. An important and very useful operator to perform the traditional search is 'like', please implement it in FilterExpressionBuilder and related classes.


## 🧵 Issue #326: Review API design of org.springframework.ai.image

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/326)


**Summary:**  
The `ImageResponse` can have more helpers to convert base64 to binary.    
  
Review for ease of use in using the `ImageResponse`   Maybe `getResponseFormat` can be an enum instead of a string


## 🧵 Issue #311: Add enumeration for all supported embedding models

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/311)


**Summary:**  



## 🧵 Issue #221: Create ResourceReader extends Function<Resource, List<Document>>

[View on GitHub](https://github.com/spring-projects/spring-ai/issues/221)


**Summary:**  
This will facilitate loading a list of `Resource`s into a vector database inside a loop.  Currently this requires recreating `TextReader` instances.
