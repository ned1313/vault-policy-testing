path "secret/data/taco" {
    capabilities = ["read"]
}

path "mykv/*" {
    capabilities = ["read","create","update"]
}