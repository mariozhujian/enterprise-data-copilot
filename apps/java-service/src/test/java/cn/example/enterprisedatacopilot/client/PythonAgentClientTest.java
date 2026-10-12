package cn.example.enterprisedatacopilot.client;


import cn.example.enterprisedatacopilot.dto.ChatRequest;
import cn.example.enterprisedatacopilot.dto.ChatResponse;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;
import java.util.UUID;

import static org.junit.Assert.*;

/**
 * @description: Java 模拟上游 Python 接口
 * @author: mario
 * @date: 2026/10/12
 */
public class PythonAgentClientTest {

    private MockWebServer server;
    private PythonAgentClient client;

    @BeforeEach
    void setup() throws IOException {
        server = new MockWebServer();
        server.start();

        WebClient webClient = WebClient.builder()
                .baseUrl(server.url("/").toString())
                .build();

        client = new PythonAgentClient(webClient);
    }

    @AfterEach
    void cleanup() throws IOException {
        server.shutdown();
    }

    @Test
    void shouldCallPythonChatApi() throws Exception {
        UUID sessionId = UUID.randomUUID();

        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .addHeader(
                        "Content-Type", "application/json"
                        )
                .setBody("""
                         {
                              "sessionId": "%s",
                              "answer": "Hello from Python",
                              "model": "fake-model"
                            }
                        
                        """.formatted(sessionId))
        );

        ChatResponse response = client.chat(new ChatRequest(sessionId, "你好"));

        assertEquals("Hello from Python", response.answer());

        assertEquals(sessionId, response.sessionId());

        var request = server.takeRequest();

        assertEquals("/chat", request.getPath());
        assertEquals("POST", request.getMethod());
        assertTrue(request.getBody().readUtf8().contains(sessionId.toString()));
    }


    @Test
    void shouldForwardSseEvents() {

        server.enqueue(new MockResponse()
                .setResponseCode(200)
                .addHeader(
                        "Content-Type",
                        "text/event-stream"
                )
                .setBody("""
                event: start
                data: {"sessionId":"test"}

                event: delta
                data: {"content":"你好"}

                event: done
                data: {"status":"completed"}

                """));

        var events = client.stream(
                new ChatRequest(UUID.randomUUID(), "你好")
        ).collectList().block();

        assertNotNull(events);
        assertEquals(3, events.size());

        assertEquals("start", events.get(0).event());
        assertEquals("delta", events.get(1).event());
        assertEquals("done", events.get(2).event());

        assertTrue(
                events.get(1).data().contains("你好")
        );
    }

}
