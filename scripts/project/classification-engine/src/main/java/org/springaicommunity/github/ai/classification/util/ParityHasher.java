package org.springaicommunity.github.ai.classification.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/**
 * SHA-256 hashing utilities for parity testing.
 * 
 * <p>Provides consistent hashing functions to compare Java and Python 
 * preprocessing results byte-for-byte. All hashes use UTF-8 encoding
 * to match Python's default behavior.</p>
 */
public class ParityHasher {
    
    private static final MessageDigest SHA256;
    
    static {
        try {
            SHA256 = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }
    
    /**
     * Compute SHA-256 hash of text using UTF-8 encoding.
     * 
     * @param text Input text to hash
     * @return Lowercase hexadecimal hash string
     */
    public static String sha256(String text) {
        if (text == null) {
            text = "";
        }
        
        synchronized (SHA256) {
            SHA256.reset();
            byte[] hash = SHA256.digest(text.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        }
    }
    
    /**
     * Hash issue text in the format expected for model input.
     * 
     * @param title Issue title
     * @param body Issue body
     * @return SHA-256 hash of "title\n\nbody"
     */
    public static String hashIssueText(String title, String body) {
        String normalizedTitle = title != null ? title : "";
        String normalizedBody = body != null ? body : "";
        String combinedText = normalizedTitle + "\n\n" + normalizedBody;
        return sha256(combinedText);
    }
    
    /**
     * Hash label list in presentation order.
     * 
     * @param labels List of labels in order
     * @return SHA-256 hash of comma-separated labels
     */
    public static String hashLabelOrder(java.util.List<String> labels) {
        String labelString = String.join(",", labels);
        return sha256(labelString);
    }
    
    /**
     * Count code blocks in text (markdown ``` patterns).
     * 
     * @param text Text to analyze
     * @return Number of code block pairs found
     */
    public static int countCodeBlocks(String text) {
        if (text == null) {
            return 0;
        }
        
        int count = 0;
        int index = 0;
        while ((index = text.indexOf("```", index)) != -1) {
            count++;
            index += 3;
        }
        return count / 2; // Pairs of opening/closing
    }
    
    /**
     * Estimate token count using simple heuristic.
     * 
     * @param text Text to analyze
     * @return Approximate token count
     */
    public static int estimateTokenCount(String text) {
        if (text == null || text.trim().isEmpty()) {
            return 0;
        }
        
        // Simple heuristic: ~4 characters per token
        return text.length() / 4;
    }
}