package com.ter.reco_backend.repository;
 
import org.springframework.data.jpa.repository.JpaRepository;

import com.ter.reco_backend.entity.Genre;
 
public interface GenreRepository extends JpaRepository<Genre, Integer> {}