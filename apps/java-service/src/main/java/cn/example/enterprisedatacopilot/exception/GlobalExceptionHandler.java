package cn.example.enterprisedatacopilot.exception;


import cn.example.enterprisedatacopilot.dto.ApiError;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

/**
 * @description: 全局异常处理
 * @author: mario
 * @date: 2026/10/9
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(value = MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleException(Exception e) {
        return ResponseEntity.badRequest().body(
                Map.of(
                        "code", "INVALID_REQUEST",
                        "message", "请求参数不合法"
                )
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handle(Exception e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(
                Map.of(
                        "code", "INTERNAL_ERROR",
                        "message", "服务暂时不可用"
                )
        );
    }

    @ExceptionHandler(value = AiUpstreamException.class)
    public ResponseEntity<ApiError> handleUpstream(AiUpstreamException ex) {
        return ResponseEntity.status(ex.getStatus()).body(
                new ApiError(  "AI_UPSTREAM_ERROR",
                        "AI服务暂时不可用"));
    }

}
