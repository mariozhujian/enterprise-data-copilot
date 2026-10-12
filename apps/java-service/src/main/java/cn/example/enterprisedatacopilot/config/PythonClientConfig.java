package cn.example.enterprisedatacopilot.config;


import io.netty.channel.ChannelOption;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

/**
 * @description: 配置 WebClient,流式请求的读取超时不是整个任务总时长
 * @author: mario
 * @date: 2026/10/12
 */
@Configuration
public class PythonClientConfig {

    @Bean
    public WebClient pythonWebClient(
            @Value("${python.agent.base-url}") String baseUrl,
            @Value("${python.agent.connect-timeout-ms}") int connectMs,
            @Value("${python.agent.response-timeout-seconds}") long responseSecs
    ) {
        HttpClient httpClient = HttpClient.create()
                // 建立 TCP 连接的超时
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectMs)
                // 响应读取相关的超时
                .responseTimeout(Duration.ofSeconds(responseSecs));

        return WebClient.builder()
                .baseUrl(baseUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();
    }

}
