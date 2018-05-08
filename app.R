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

plotType <- function(df, type, bins, probab) {
  switch(type,
         A = hist(df$hitsPer100k,  main = paste("Histogram of", "normalised freq."), xlab = "No. of hits in corpus", ylab="Freq. per 100,000 words", breaks=bins, border="blue", col="khaki", probability = probab),
         B = hist(log(df$hitsPer100k), main = paste("Histogram of", "normalised freq. (log values)"), xlab = "No. of hits in the corpus", ylab="Freq. per 100,000 words", breaks=bins, border="blue", col="khaki3", probability = probab),
         C = hist(df, main = paste("Histogram of", "normalised freq. (trimmed 5%)"), xlab = "No. of of hits in the corpus", ylab="Freq. per 100,000 words", breaks=bins, border="blue", col="moccasin", probability = probab),
         D = hist(log(df), main = paste("Histogram of", "normalised freq. (trimmed 5% log values)"), xlab = "No. of of hits in the corpus", ylab="Freq. per 100,000 words", breaks=bins, border="blue", col="moccasin", probability = probab))
}

shapiroType <- function(hPk, type) {
  switch(type,
         A = shapiro.test(hPk),
         B = shapiro.test(log(hPk)),
         C = shapiro.test(hPk),
         D = shapiro.test(log(hPk)))
}

qqplotType <- function(hPk, type) {
  switch(type,
         A = list(qqnorm(hPk), qqline(hPk)),
         B = list(qqnorm(log(hPk)), qqline(log(hPk))),
         C = "",
         D = "")
}

#runApp(list(
  ui = fluidPage(
#    textOutput('text')
    titlePanel("The Shiny Corpus of British Fiction"),
    sidebarLayout(
      sidebarPanel(
#        
# Input: Slider for the number of bins ----
        sliderInput(inputId = "nobins",
                    label = h4("Number of bins:"),
                    min = 5,
                    max = 35,
                    value = 15,
                    step = 10),
        radioButtons("pType", label = h4("Histogram (Density)"),
             choices = list("Normal" = "A", "Log" = "B", "Trim 5%" = "C", "Trim 5% & Log" = "D"), 
             selected = "A"),
        checkboxInput('densitycheckbox', label = "Density (Norm. and Log only)", value = FALSE),
    width = 2),
    mainPanel(
        verbatimTextOutput('summary'),
        plotOutput('hist'),
        verbatimTextOutput('shapiro'),
        plotOutput('qqplot'),
#        plotOutput('log'),
#        verbatimTextOutput('shapirolog'),
#        plotOutput('qqplotlog'),
#        plotOutput('trim'),
#        verbatimTextOutput('shapirotrim'),
#        plotOutput('trimlog'),
#        plotOutput('boxplot'),
#        verbatimTextOutput('kruskal'),
#        verbatimTextOutput('wpairwise'),
#        plotOutput('boxplotlog'),
#        plotOutput('genderboxplot'),
#        verbatimTextOutput('wilcoxon'),
#        verbatimTextOutput('kruskallog')
    width = 6),
  fluid = TRUE, position = "left")
  )
    server = function(input, output, session) {
    output$summary <- renderPrint({
      df <- getURLarg(session)
      summary(df$hitsPer100k)
    })
      output$hist <- renderPlot({
      df <- getURLarg(session)
      if (input$pType == "C" | input$pType == "D") {
        dtfn <- df$hitsPer100k
        dtfl <- length(dtfn)
        dtfls <- sort(dtfn)
        trimfraction <- as.integer(dtfl * 0.05)
        df <- Trim(dtfls, trim=trimfraction)        
      }
      plotType(df, input$pType, input$nobins, TRUE)
      if (input$densitycheckbox == TRUE & input$pType == "A") {
      lines(density(df$hitsPer100k), lwd = 2)
      lines(density(df$hitsPer100k, adjust = 2), lty = "dotted")
      }
      else if (input$densitycheckbox == TRUE & input$pType == "B") {
        lines(density(log(df$hitsPer100k)), lwd = 2)
        lines(density(log(df$hitsPer100k), adjust = 2), lty = "dotted")
      }
    })
      output$shapiro <- renderPrint({
        df <- getURLarg(session)
        hitsPer100k <- df$hitsPer100k
        if (input$pType == "C" | input$pType == "D") {
          dtfn <- df$hitsPer100k
          dtfl <- length(dtfn)
          dtfls <- sort(dtfn)
          trimfraction <- as.integer(dtfl * 0.05)
          hitsPer100k <- Trim(dtfls, trim=trimfraction)
        }
        shapiroType(hitsPer100k, input$pType)
    })
      output$qqplot <- renderPlot({
        df <- getURLarg(session)
        hitsPer100k <- df$hitsPer100k
        qqplotType(hitsPer100k, input$pType)
#        qqnorm(df$hitsPer100k)
#        qqline(df$hitsPer100k)
      })
    output$log <- renderPlot({
      df <- getURLarg(session)
      hist(log(df$hitsPer100k), main = paste("Histogram of", "normalised freq. (log values)"), xlab = "No. of hits in the corpus", ylab="Freq. per 100,000 words", breaks=input$nobins, border="blue", col="khaki3")
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
      hist(dtf2, main = paste("Histogram of", "normalised freq. (trimmed 5%)"), xlab = "No. of of hits in the corpus", ylab="Freq. per 100,000 words", breaks=input$nobins, border="blue", col="moccasin", probability = TRUE)
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
      hist(log(dtf2), main = paste("Histogram of", "normalised freq. (trimmed 5% and log values)"), xlab = "No. of of hits in the corpus", ylab="Freq. per 100,000 words", breaks=20, border="green", col="orange", probability = TRUE)
    })
    output$boxplot <- renderPlot({
      df <- getURLarg(session)
      boxplot(hitsPer100k ~ tertial, data = df, main = 'Hits/Tertial', notch = FALSE, col = c('powderblue', 'mistyrose'))
    })
    output$kruskal <- renderPrint({
      df <- getURLarg(session)
      kruskal.test(hitsPer100k ~ as.factor(tertial), data=df)    
    })
    output$wpairwise <- renderPrint({
      df <- getURLarg(session)
      pairwise.wilcox.test(df$hitsPer100k, as.factor(df$tertial), p.adjust.method = "BH")    
    })
    output$boxplotlog <- renderPlot({
      df <- getURLarg(session)
      boxplot(log(hitsPer100k) ~ tertial, data = df, main = 'log(Hits)/Tertial', notch = FALSE, col = c('blue', 'cyan'))
    })
    output$kruskallog <- renderPrint({
      df <- getURLarg(session)
      kruskal.test(log(hitsPer100k) ~ as.factor(tertial), data=df)    
    })
    output$genderboxplot <- renderPlot({
      df <- getURLarg(session)
      boxplot(hitsPer100k ~ gender, data = df, main = 'Hits/Gender', notch = FALSE, col = c('powderblue', 'mistyrose'))
    })
    output$wilcoxon <- renderPrint({
      df <- getURLarg(session)
      wilcox.test(log(hitsPer100k) ~ as.factor(gender), data=df)    
    })
  }
shinyApp(ui, server)

#To run
#runApp("shiny/cqp/", port = 6989, launch.browser = FALSE)
#library(shiny)
#runApp("shiny/test2/", display.mode = "showcase", port = 6989, launch.browser = FALSE)

