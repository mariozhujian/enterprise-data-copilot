package cn.example.enterprisedatacopilot.exception;


import org.springframework.http.HttpStatusCode;

/**
 * @description: 自定义上游异常
 * @author: mario
 * @date: 2026/10/12
 */
public class AiUpstreamException extends RuntimeException {

    private final HttpStatusCode status;

    public AiUpstreamException(HttpStatusCode status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatusCode getStatus() {
        return status;
    }

}
