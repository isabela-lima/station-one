/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2882744473")

  // update collection data
  unmarshal({
    "name": "items"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2882744473")

  // update collection data
  unmarshal({
    "name": "type"
  }, collection)

  return app.save(collection)
})
