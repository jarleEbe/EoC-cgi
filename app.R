library(shiny)
library(jsonlite)
library(stringr)
library(stats)
library(DescTools)

getURLarg <- function(session) {
  query <- parseQueryString(session$clientData$url_search)
  myArgsString <- paste(names(query), query, sep = "=", collapse=", ")
  myArgsVektor <- strsplit(myArgsString, "&")[[1]]
  myValue <- myArgsVektor[1]
  myArgument <- str_replace(myValue, "^([a-z]+?)=", "")
  parameterfile = "http://localhost/hf/ilos/cbf/cache/"
  parameterfile = paste0(parameterfile,myArgument)
  df <- fromJSON(url(parameterfile))
  return(df)
#  dtf <- fromJSON(myArgument)
#  return(dtf)
}

runApp(list(
  ui = fluidPage(
#    textOutput('text')
    titlePanel("The Shiny Corpus of British Fiction"),
    sidebarLayout(position = "left",
      sidebarPanel = (
#        sliderInput("Obs", "Number of obs", min = 1, max = 500, value = 250)
        ""
      ),
      mainPanel(
        verbatimTextOutput('summary'),
        plotOutput('hist'),
        verbatimTextOutput('shapiroraw'),
        plotOutput('qqplot'),
        plotOutput('log'),
        verbatimTextOutput('shapirolog'),
        plotOutput('qqplotlog'),
        plotOutput('trim'),
#        verbatimTextOutput('shapirotrim'),
        plotOutput('trimlog'),
        plotOutput('boxplot'),
        verbatimTextOutput('kruskal'),
        plotOutput('boxplotlog'),
        verbatimTextOutput('kruskallog')
      )
    )
  ),
  server = function(input, output, session) {
#    query <- parseQueryString(session$clientData$url_search)
    output$summary <- renderPrint({
      df <- getURLarg(session)
      summary(df$hitsPer100k)
    })
      output$hist <- renderPlot({
      df <- getURLarg(session)
      hist(df$hitsPer100k,  main = paste("Histogram of", "normalised freq."), xlab = "Numb hits in corpus", ylab="Freq. per 100,000 words", breaks = 20, border="blue", col="khaki", probability = TRUE)
      lines(density(df$hitsPer100k))
      lines(density(df$hitsPer100k, adjust = 2), lty = "dotted")
    })
      output$shapiroraw <- renderPrint({
        df <- getURLarg(session)
        hitsPer100k <- df$hitsPer100k
        shapiro.test(hitsPer100k)
    })
      output$qqplot <- renderPlot({
        df <- getURLarg(session)
        qqnorm(df$hitsPer100k)
        qqline(df$hitsPer100k)
      })
    output$log <- renderPlot({
      df <- getURLarg(session)
      hist(log(df$hitsPer100k), main = paste("Histogram of", "normalised freq. (log values)"), xlab = "Numb hits in the corpus", ylab="Freq. per 100,000 words", breaks=20, border="blue", col="khaki3", probability = TRUE)
    })
    output$shapirolog <- renderPrint({
      df <- getURLarg(session)
      hitsPer100k <- df$hitsPer100k
      shapiro.test(log(hitsPer100k))
    })
    output$qqplotlog <- renderPlot({
      df <- getURLarg(session)
      qqnorm(log(df$hitsPer100k))
      qqline(log(df$hitsPer100k))
    })
    output$trim <- renderPlot({
      df <- getURLarg(session)
      dtfn <- df$hitsPer100k
      dtfl <- length(dtfn)
      dtfls <- sort(dtfn)
      trimfraction <- as.integer(dtfl * 0.05)
      dtf2 <- Trim(dtfls, trim=trimfraction)
      hist(dtf2, main = paste("Histogram of", "normalised freq. (trimmed 5%)"), xlab = "Numb of hits in the corpus", ylab="Freq. per 100,000 words", breaks=20, border="blue", col="moccasin", probability = TRUE)
    })
    output$shapirotrim <- renderPrint({
      df <- getURLarg(session)
      hitsPer100k <- df$hitsPer100k
      dtfn <- df$hitsPer100k
      dtfl <- length(dtfn)
      dtfls <- sort(dtfn)
      trimfraction <- as.integer(dtfl * 0.05)
      trimhitsPer100k <- Trim(dtfls, trim=trimfraction)
      shapiro.test(trimhitsPer100k)
    })
    output$trimlog <- renderPlot({
      df <- getURLarg(session)
      dtfn <- df$hitsPer100k
      dtfl <- length(dtfn)
      dtfls <- sort(dtfn)
      trimfraction <- as.integer(dtfl * 0.05)
      dtf2 <- Trim(dtfls, trim=trimfraction)
      hist(log(dtf2), main = paste("Histogram of", "normalised freq. (trimmed 5% and log values)"), xlab = "Numb of hits in the corpus", ylab="Freq. per 100,000 words", breaks=20, border="green", col="orange", probability = TRUE)
    })
    output$boxplot <- renderPlot({
      df <- getURLarg(session)
      boxplot(df$hitsPer100k ~ df$tertial, data = df, main = 'Hits/Tertial', notch = TRUE, col = c('powderblue', 'mistyrose'))
    })
    output$kruskal <- renderPrint({
      df <- getURLarg(session)
      kruskal.test(df$hitsPer100k ~ as.factor(df$tertial), data=df)    
    })
    output$boxplotlog <- renderPlot({
      df <- getURLarg(session)
      boxplot(log(df$hitsPer100k) ~ df$tertial, data = df, main = 'log(Hits)/Tertial', notch = TRUE, col = c('blue', 'cyan'))
    })
    output$kruskallog <- renderPrint({
      df <- getURLarg(session)
      kruskal.test(log(df$hitsPer100k) ~ as.factor(df$tertial), data=df)    
    })
  }
), port = 6989, launch.browser = FALSE)
