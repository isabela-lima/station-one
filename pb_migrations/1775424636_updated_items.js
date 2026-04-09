/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2882744473")

  // add field
  collection.fields.addAt(6, new Field({
    "hidden": false,
    "id": "bool1655102503",
    "name": "priority",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "bool"
  }))

  // add field
  collection.fields.addAt(7, new Field({
    "hidden": false,
    "id": "date3275789471",
    "max": "",
    "min": "",
    "name": "dueDate",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "date"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2882744473")

  // remove field
  collection.fields.removeById("bool1655102503")

  // remove field
  collection.fields.removeById("date3275789471")

  return app.save(collection)
})
