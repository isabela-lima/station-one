/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3863458068")

  // update collection data
  unmarshal({
    "createRule": "@request.auth.id = user",
    "deleteRule": "@request.auth.id = user",
    "listRule": "@request.auth.id = user",
    "updateRule": "@request.auth.id = user",
    "viewRule": "@request.auth.id = user"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3863458068")

  // update collection data
  unmarshal({
    "createRule": "goal.user = @request.auth.id",
    "deleteRule": "goal.user = @request.auth.id",
    "listRule": "goal.user = @request.auth.id",
    "updateRule": "goal.user = @request.auth.id",
    "viewRule": "goal.user = @request.auth.id"
  }, collection)

  return app.save(collection)
})
