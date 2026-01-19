import './CommonEntitiesList.css'

function CommonEntitiesList({ entities, onEntityClick }) {
  if (!entities || entities.length === 0) {
    return (
      <div className="common-entities">
        <h3>👥 Common Entities</h3>
        <div className="no-entities">No entities extracted yet</div>
      </div>
    )
  }

  return (
    <div className="common-entities">
      <h3>👥 Common Entities</h3>
      <div className="entities-list">
        {entities.map((entity, index) => (
          <div
            key={index}
            className="entity-item"
            onClick={() => onEntityClick && onEntityClick(entity.value)}
          >
            <div className="entity-name">{entity.value}</div>
            <div className="entity-frequency">{entity.frequency} mentions</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CommonEntitiesList
