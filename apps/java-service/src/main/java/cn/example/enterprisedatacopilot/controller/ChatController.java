package cn.example.enterprisedatacopilot.controller;


import cn.example.enterprisedatacopilot.dto.AnalysisResult;
import cn.example.enterprisedatacopilot.dto.ChatRequest;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import cn.example.enterprisedatacopilot.service.ChatService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }


    @PostMapping
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return chatService.chat(request.message());
    }

    @PostMapping("/analyze")
    public AnalysisResult analyze(@RequestBody ChatRequest request) {
        return chatService.analyze(request.message());
    }

}
