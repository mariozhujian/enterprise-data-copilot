package cn.example.enterprisedatacopilot.controller;


import cn.example.enterprisedatacopilot.dto.ChatRequest;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import cn.example.enterprisedatacopilot.service.ChatService;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.*;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
public class ChatControllerTest {

//    private final ChatService chatService = mock(ChatService.class);
//
//    private final ChatController chatController = new ChatController(chatService);
//
//    @Test
//    void shouldReturnChatResponse() {
//        when(chatService.chat("你好"))
//                .thenReturn(new ChatResponse("你好，我是 AI 助手"));
//
//        ChatResponse result = chatController.chat(new ChatRequest("你好"));
//
//        assertEquals("你好，我是 AI 助手", result.answer());
//
//        verify(chatService, times(1)).chat("你好");
//    }
//
//    @Test
//    void shouldPropagateServiceFailure() {
//        when(chatService.chat("测试"))
//                .thenThrow(new RuntimeException("Model unavailable"));
//
//        assertThrows(RuntimeException.class, () -> chatController.chat(new ChatRequest("测试")));
//    }
}
