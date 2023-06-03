from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, models, database, oauth2
from sqlalchemy.orm import Session


router = APIRouter(
    prefix='/rsvp',
    tags=['Rsvp']
)

@router.post('/')
def rsvp(rsvp: schemas.Rsvp, db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == rsvp.event_id).first()
    rsvp_query = db.query(models.Rsvp).filter(models.Rsvp.event_id == rsvp.event_id, models.Rsvp.user_id == current_user.id)
    found_rsvp = rsvp_query.first()

    if not event:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event doesn't exist!! ")
    

    if rsvp.dir == 1:
        if found_rsvp:
            return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already rsvp'd !!")
        
        new_rsvp = models.Rsvp(event_id=rsvp.event_id, user_id=current_user.id)
        db.add(new_rsvp)
        db.commit()

        return {"msg": "Sucessfully registered for the event! Congrats!! "}
    
    else:
        if not found_rsvp:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doesn't exist")
        
        rsvp_query.delete()
        db.commit()

        return {"msg": "Canceled the registration!! "}