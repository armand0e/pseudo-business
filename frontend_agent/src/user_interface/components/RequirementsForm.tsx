import { useState, type FC, type FormEvent } from 'react';

const RequirementsForm: FC = () => {
    const [description, setDescription] = useState('');

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        // In a real application, you would dispatch an action
        // to submit the requirements to the backend.
        console.log('Submitted requirements:', { description });
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="description">Project Description</label>
                <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
            </div>
            <button type="submit">Submit Requirements</button>
        </form>
    );
};

export default RequirementsForm;