package com.ter.reco_backend.controller;

import com.ter.reco_backend.entity.Item.ItemType;
import com.ter.reco_backend.repository.RecommendationRepository;
import com.ter.reco_backend.service.PythonEngineService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/recommendations")
public class RecommendationController {

    private final RecommendationRepository recommendationRepository;
    private final PythonEngineService pythonEngineService;

    public RecommendationController(RecommendationRepository recommendationRepository,
                                    PythonEngineService pythonEngineService) {
        this.recommendationRepository = recommendationRepository;
        this.pythonEngineService = pythonEngineService;
    }

    @GetMapping("/me")
    public ResponseEntity<?> myRecommendations(
            @RequestParam(required = false) String type,
            Authentication auth) {
        String userId = auth.getName();
        if (type != null) {
            return ResponseEntity.ok(
                recommendationRepository.findByUserIdAndType(userId, ItemType.valueOf(type)));
        }
        return ResponseEntity.ok(recommendationRepository.findByUserIdOrderByScoreDesc(userId));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> checkPythonHealth() {
        boolean healthy = pythonEngineService.isHealthy();
        return ResponseEntity.ok(Map.of(
            "python_engine", healthy ? "up" : "down"
        ));
    }

    @GetMapping("/live/{userId}")
    public ResponseEntity<Map> getLiveRecommendations(
            @PathVariable String userId,
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "10") int topN) {
        Map result = pythonEngineService.getRecommendations(userId, type, topN);
        return ResponseEntity.ok(result);
    }
}