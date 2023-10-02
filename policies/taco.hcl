path "secret/data/taco" {
    capabilities = ["read"]
}

path "secret/data/+/taco/*" {
    capabilities = ["create","list","update","delete","read"]
}

path "mykv/*" {
    capabilities = ["read","create","update"]
}