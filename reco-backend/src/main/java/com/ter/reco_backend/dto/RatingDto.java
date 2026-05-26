package com.ter.reco_backend.dto;

public record RatingDto(
    String id,
    String itemId,
    float score
) {}