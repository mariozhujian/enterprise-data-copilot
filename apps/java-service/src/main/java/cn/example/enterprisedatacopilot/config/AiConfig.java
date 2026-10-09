package cn.example.enterprisedatacopilot.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * @description: 创建 ChatClient 配置
 * ChatClient 可以理解为 Spring AI 对模型调用的高级封装，提供Prompt构建、同步调用、流式调用和结构化结果转换等能力。
 * @author: mario
 * @date: 2026/10/9
 */
@Configuration
public class AiConfig {

    @Bean
    public ChatClient chatClient(ChatClient.Builder builder) {
        return builder.defaultSystem(
                """
                    你是企业级智能数据分析助手。

                    规则：
                    1. 使用简体中文回答。
                    2. 不得编造企业内部数据。
                    3. 缺少业务数据时明确说明。
                    4. 当前阶段不具备数据库查询能力。
                """
        ).build();
    }

}
