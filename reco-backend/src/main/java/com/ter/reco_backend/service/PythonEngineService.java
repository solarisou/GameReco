package com.ter.reco_backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.Map;
import java.util.List;

@Service
public class PythonEngineService {

    private final RestTemplate restTemplate;

    @Value("${python.engine.url:http://localhost:5000}")
    private String pythonEngineUrl;

    public PythonEngineService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                pythonEngineUrl + "/health", Map.class
            );
            return response.getStatusCode() == HttpStatus.OK;
        } catch (Exception e) {
            return false;
        }
    }

    public Map getRecommendations(String userId, String type, int topN) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = Map.of(
            "user_id", userId,
            "type", type != null ? type : "",
            "top_n", topN
        );

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
            pythonEngineUrl + "/recommend",
            HttpMethod.POST,
            entity,
            Map.class
        );

        return response.getBody();
    }
}