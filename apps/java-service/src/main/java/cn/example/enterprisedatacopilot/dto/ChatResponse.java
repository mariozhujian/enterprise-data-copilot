package cn.example.enterprisedatacopilot.dto;


import java.util.UUID;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
public record ChatResponse(
        UUID sessionId,
        String answer,
        String model
) {}
