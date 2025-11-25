
library(ape)
library(ggplot2)
library(ggtree)
library(treeio)
################################
# Re-root the tree
################################
tree <- read.tree("1.nwk")
tree_rooted <- root(tree, outgroup = "OUT", resolve.root = TRUE)
write.tree(tree_rooted, file = "1_rooted.nwk")

## Set working directory
setwd("script")
## Load tree file
WGS_tree <- read.tree("WGS.tree")

## File paths can be modified as needed
group_file      <- "../conf/group.txt" #! First column: label (ID), second column: group, no header
color_file      <- "../conf/color.csv" #! First column: group, second column: color, no header
# Read group information
group_df        <- read.table(group_file, 
                              header = FALSE, 
                              sep = "\t", 
                              stringsAsFactors = FALSE, 
                              col.names = c("label", "group"))
group_list      <- split(group_df$label, group_df$group) # Convert group info to list
# Read color information
color_df        <- read.table(color_file, header = FALSE, sep = ",", stringsAsFactors = FALSE, comment.char = '', col.names = c("group", "color"))
group_colors    <- setNames(color_df$color, color_df$group) # Convert color info to named vector

## Read tree and assign groups
tree_grouped <- groupOTU(WGS_tree, group_list)
## ================Draw phylogenetic tree using ggtree================
## Draw phylogenetic tree using ggtree
p0 <- ggtree(
    tree_grouped,                                   #* Phylogenetic tree object
    aes(color = group),                             #* Branch color
    layout = 'fan',                                 #* Layout
    open.angle = 5,                                 #* Open angle
    lwd = 0.2                                       #* Branch width
) +
scale_color_manual(values = group_colors) +        #* Remove this line if no branch coloring is needed
geom_tiplab(
  size = 0.5,                                     #* Tip label font size
  align = TRUE,                                   #* Align tip labels
  hjust = -0.5                                    #* Horizontal adjustment
) +
geom_nodepoint(size = 0.3, alpha = 0.5) +          #* Add node points
geom_nodelab(
  aes(label = round(branch.length, 3)),           #* branch.length label
  hjust = -0.3,                                   #* Horizontal adjustment
  size = 0.7                                      #* Font size
) +
geom_nodelab(
  aes(label = round(node_to_tip_distance[node], 3)), #* Node-to-tip distance
  hjust = 1,                                      #* Horizontal adjustment
  color = "#000000",                              #* Color (black)
  size = 0.7                                      #* Font size
)


## Save plot
ggsave(p0, filename = '../output/tree.pdf', units = "cm", height = 20, width = 15 )

library(ggtree)
library(ggtreeExtra)
library(tidyverse)
library(ggstar)
library(ggtreeExtra)
library(ggridges)
library(ggnewscale)
library(treeio)

df_META <- read.csv("../data/df_META.csv") #* Read metadata file

p2 <- p0 +
  new_scale_fill() +
  geom_fruit(
    data = df_META,
    geom = geom_tile, #* geom_tile for heatmap
    mapping = aes(y = ID, fill = Continent), #* Can be replaced with Country or other categorical variable
    offset = 0.08, #* Heatmap offset
    colour = "white", #* Heatmap border color
    linewidth = 0.2, #* Heatmap border width
    pwidth = 0.25, #* Heatmap width
    axis.params = list(axis = "x", text.angle = -45, hjust = 0) #* x axis parameters
  ) 
p2 <- p0 +
  new_scale_fill() +
  geom_fruit(
    data = df_META,
    geom = geom_tile, 
    offset = 0.08, 
    colour = "white",
    linewidth = 0.2, 
    pwidth = 0.25, 
    axis.params = list(axis = "x", text.angle = -45, hjust = 0) 
  ) 

p3 <- p2 +
  new_scale_fill() +
  geom_fruit(
    data = df_META,
    geom = geom_tile,
    mapping = aes(y = ID,  fill = Latitude), #* Add other continuous variables such as Longitude, altitude, etc.
    pwidth = 0.15,
    axis.params = list(axis = "x", text.angle = -45, hjust = 0)
  ) 
p3 <- p2 +
  new_scale_fill() +
  geom_fruit(
    data = df_META,
    geom = geom_tile,
    mapping = aes(y = ID,  fill = Latitude), #* 在此基础上添加Longitude、altitude等其他连续变量
    pwidth = 0.15,
    axis.params = list(axis = "x", text.angle = -45, hjust = 0)
  ) 

## Save final plot
ggsave(p3, filename = '../output/tree_with_META.pdf')