package cn.example.enterprisedatacopilot.dto;


import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
public record ChatRequest(
        @NotBlank(message = "问题不能为空")
        @Size(max = 4000, message = "问题不能超过4000字符")
        String message
) {}
