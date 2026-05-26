package com.ter.reco_backend.dto;

import com.ter.reco_backend.entity.Wishlist;

public class WishlistDto {
    public String id;
    public String addedAt;
    public ItemDto item;

    public static class ItemDto {
        public String id;
        public String title;
        public String type;
        public String synopsis;
        public String coverUrl;
        public Float  avgRating;
    }

    public static WishlistDto from(Wishlist w) {
        WishlistDto dto  = new WishlistDto();
        dto.id           = w.getId();
        dto.addedAt      = w.getAddedAt() != null ? w.getAddedAt().toString() : null;

        ItemDto itemDto  = new ItemDto();
        itemDto.id       = w.getItem().getId();
        itemDto.title    = w.getItem().getTitle();
        itemDto.type     = w.getItem().getType().name();
        itemDto.synopsis = w.getItem().getSynopsis();
        itemDto.coverUrl = w.getItem().getCoverUrl();
        itemDto.avgRating = w.getItem().getAvgRating();
        dto.item         = itemDto;

        return dto;
    }
}