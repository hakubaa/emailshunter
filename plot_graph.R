library('igraph')

setwd("/media/Data/Projects/emailshunter")

dataset <- read.csv("graph.csv", sep = ";", stringsAsFactors = FALSE)
urls <- unique(c(dataset$from, dataset$to))
ids <- paste0("s", 1:length(urls))
nodes <- data.frame(id=ids, url=urls)
rownames(nodes) <- urls
links <- data.frame(from = nodes[dataset$from,]$id, 
                    to = nodes[dataset$to,]$id)

dataset$from <- factor(dataset$from, levels=urls)
dataset$to <- factor(dataset$to, levels=urls)

net <- graph_from_data_frame(d=links, vertices=nodes, directed=TRUE) 

# Remove loops in the graph
net <- simplify(net, remove.multiple = F, remove.loops = T) 

plot(net, edge.arrow.size=.4,vertex.label=NA)
