package cn.example.enterprisedatacopilot.controller;


import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * @description: TODO
 * @author: mario
 * @date: 2026/10/9
 */
@RestController
public class HealthController {

    @GetMapping
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

}
