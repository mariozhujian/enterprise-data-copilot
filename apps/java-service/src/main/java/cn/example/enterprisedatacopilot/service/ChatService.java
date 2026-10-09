package cn.example.enterprisedatacopilot.service;


import cn.example.enterprisedatacopilot.dto.AnalysisResult;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
@Service
public class ChatService {

    private final ChatClient chatClient;

    public ChatService(ChatClient chatClient) {
        this.chatClient = chatClient;
    }

    public ChatResponse chat(String message) {
        String answer = chatClient
                .prompt()
                .user(message)
                .call()
                .content();

        return new ChatResponse(answer);
    }

    public AnalysisResult analyze(String message) {
        return chatClient
                .prompt()
                .system("""
                        你是企业数据分析意图识别器
                        
                        只分析用户问题，不查询数据库。
                        
                        intent 必须是以下之一：
                        QUERY、ANALYZE、CHAT、UNKNOWN。
    
                        metric 填写业务指标名称；
                        timeRange 填写时间范围；
                        explanation 简要解释识别结果。
    
                        不确定的字段填写空字符串。
                        """)
                .user(message)
                .call()
                .entity(AnalysisResult.class);
    }
}
