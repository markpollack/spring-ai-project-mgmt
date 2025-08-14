package org.springaicommunity.github.ai.collection;

import java.util.ArrayList;
import java.util.List;

/**
 * Parsed configuration result from command-line arguments.
 */
public class ParsedConfiguration {
    // Repository settings
    public String repository;
    
    // Batch configuration
    public int batchSize;
    
    // Mode flags
    public boolean dryRun = false;
    public boolean incremental = false;
    public boolean zip = false;
    public boolean verbose = false;
    public boolean clean = true; // Default to clean mode
    public boolean resume = false;
    public boolean helpRequested = false;
    
    // Issue filtering
    public String issueState;
    public List<String> labelFilters = new ArrayList<>();
    public String labelMode;
    
    public ParsedConfiguration(CollectionProperties defaultProperties) {
        // Initialize with defaults
        this.repository = defaultProperties.getDefaultRepository();
        this.batchSize = defaultProperties.getBatchSize();
        this.issueState = defaultProperties.getDefaultState();
        this.labelMode = defaultProperties.getDefaultLabelMode();
        this.verbose = defaultProperties.isVerbose();
    }
    
    @Override
    public String toString() {
        return "ParsedConfiguration{" +
                "repository='" + repository + '\'' +
                ", batchSize=" + batchSize +
                ", dryRun=" + dryRun +
                ", incremental=" + incremental +
                ", zip=" + zip +
                ", verbose=" + verbose +
                ", clean=" + clean +
                ", resume=" + resume +
                ", helpRequested=" + helpRequested +
                ", issueState='" + issueState + '\'' +
                ", labelFilters=" + labelFilters +
                ", labelMode='" + labelMode + '\'' +
                '}';
    }
}