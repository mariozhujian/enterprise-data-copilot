package cn.example.enterprisedatacopilot.client;


import cn.example.enterprisedatacopilot.dto.ChatRequest;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import cn.example.enterprisedatacopilot.exception.AiUpstreamException;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;

import java.time.Duration;

/**
 * @description: Java 和 Python 之间最重要的客户端类
 * @author: mario
 * @date: 2026/10/12
 */
@Component
public class PythonAgentClient {

    private final WebClient webClient;

    public PythonAgentClient(WebClient pythonWebClient) {
        this.webClient = pythonWebClient;
    }

    /**
     * 同步调用 Python Agent
     *
     * 由于当前服务是 Spring MVC
     * 普通接口使用 block() 等待完整响应
     * @param request 请求
     * @return 响应
     */
    public ChatResponse chat(ChatRequest request) {
        try {
            ChatResponse response = webClient.post()
                    .uri("/chat")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    // bodyToMono(String.class) 会尝试把流式内容当作一个完整响应处理，失去实时分块输出的意义
                    .bodyToMono(ChatResponse.class)
                    .block(Duration.ofSeconds(90));

            if (response == null) {
                throw new AiUpstreamException(
                        HttpStatus.BAD_GATEWAY,
                        "Python Agent 返回空响应"
                );
            }
            return response;
        } catch (WebClientResponseException e) {
            throw new AiUpstreamException(
                    HttpStatus.BAD_GATEWAY,
                    "Python Agent HTTP error: " + e.getStatusCode()
            );
        }
    }

    /**
     * 转发 Python SSE，保留原始事件名称和 JSON 数据。
     */
    public Flux<ServerSentEvent<String>> stream(ChatRequest request) {
        return webClient.post()
                .uri("/chat/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(request)
                .retrieve()
                .bodyToFlux(
                        new ParameterizedTypeReference<ServerSentEvent<String>>() {
                        }
                )
                .onErrorResume(error -> {
                    if (error instanceof java.util.concurrent.CancellationException) {
                        return Flux.error(error);
                    }
                    return Flux.just(
                            ServerSentEvent.<String>builder()
                                    .event("error")
                                    .data("""
                                            {"code":"AI_UPSTREAM_ERROR",
                                             "message":"Python Agent流式调用失败"}
                                            """.trim())
                                    .build()
                    );
                });
    }

}
