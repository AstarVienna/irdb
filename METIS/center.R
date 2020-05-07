center <- function(d){
    sum(d$wavelength * d$transmission) / sum(d$transmission)
}
