import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheckCircle, faHome, faSearch, faRedo } from '@fortawesome/free-solid-svg-icons';

const BulkIndexingSuccess = () => {
  // You might want to get some stats from URL params or context
  // For example: const location = useLocation(); const { documentCount } = location.state || {};
  
  return (
    <Container className="py-5">
      <Row className="justify-content-center">
        <Col md={8}>
          <Card className="shadow-sm">
            <Card.Body className="text-center p-5">
              <div className="mb-4">
                <FontAwesomeIcon 
                  icon={faCheckCircle} 
                  className="text-success" 
                  style={{ fontSize: '5rem' , color: '#28a745' }} 
                />
              </div>
              
              <h2 className="mb-3">Bulk Indexing Successfully Completed!</h2>
              
              <p className="lead text-muted mb-4">
                Your NetSuite documents have been successfully indexed in Glean and are now searchable.
              </p>
              

              <div className="d-flex flex-column flex-md-row justify-content-center gap-3">
                <Button 
                  as={Link} 
                  to="/" 
                  variant="outline-primary" 
                  size="lg" 
                  className="px-4"
                >
                  <FontAwesomeIcon icon={faHome} className="me-2" />
                  Back to Home
                </Button>
                
                <Button 
                  as="a" 
                  href="https://app.glean.com/search" 
                  target="_blank" 
                  variant="outline-success" 
                  size="lg" 
                  className="px-4"
                >
                  <FontAwesomeIcon icon={faSearch} className="me-2" />
                  Go to Glean Search
                </Button>
                
               

              </div>
            </Card.Body>
          </Card>

        </Col>
      </Row>
    </Container>
  );
};

export default BulkIndexingSuccess;