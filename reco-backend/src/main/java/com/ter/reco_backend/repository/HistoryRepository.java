package com.ter.reco_backend.repository;
 
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.ter.reco_backend.entity.History;
 
public interface HistoryRepository extends JpaRepository<History, String> {
    List<History> findByUserIdOrderByViewedAtDesc(String userId);
}