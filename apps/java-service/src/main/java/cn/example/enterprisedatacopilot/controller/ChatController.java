package cn.example.enterprisedatacopilot.controller;


import cn.example.enterprisedatacopilot.client.PythonAgentClient;
import cn.example.enterprisedatacopilot.dto.AnalysisResult;
import cn.example.enterprisedatacopilot.dto.ChatRequest;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import cn.example.enterprisedatacopilot.service.ChatService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.util.UUID;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final PythonAgentClient pythonClient;
    private final ChatService chatService;

    public ChatController(PythonAgentClient pythonClient, ChatService chatService) {
        this.pythonClient = pythonClient;
        this.chatService = chatService;
    }

    private ChatRequest ensureSession(ChatRequest request) {
        UUID id = request.sessionId() == null ? UUID.randomUUID() : request.sessionId();
        return new ChatRequest(id, request.message());
    }


    @PostMapping
    public ChatResponse chat(@Valid @RequestBody ChatRequest request) {
        return pythonClient.chat(request);
    }

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream(@Valid @RequestBody ChatRequest request) {
        return pythonClient.stream(ensureSession(request));
    }


    @PostMapping("/analyze")
    public AnalysisResult analyze(@Valid @RequestBody ChatRequest request) {
        return chatService.analyze(request.message());
    }

}
